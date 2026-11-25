"""Flask interface for the ETF allocation demonstration (Shahmeer).

Layers: routes (this file) -> business logic (src/biz) -> data access.
Milestone 5: the default data access layer is the knowledge graph
(src/semantic: SPARQL over an embedded Oxigraph store, with the ontology and
Mason's native graph validator attached by semantic.runtime). The accepted M4
SQLite layer (src/dal) stays selectable with BACKEND='sql' for regression tests.

This module contains no SQL and no SPARQL. It reads request data, calls biz and
data-access functions, and turns results or errors into pages and messages.
Both data-access layers expose the same function names, arguments, result
dictionaries and error classes, so every route is written once.
"""
import argparse
import os
import sys
import threading
from contextlib import contextmanager
from itertools import zip_longest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from biz import disclosures as biz
from dal import lookups as sql_lookups, repositories as sql_repositories
from dal.database import DEFAULT_DB_PATH, Database
from semantic import lookups as graph_lookups, repositories as graph_repositories

# Error classes are shared by both layers (semantic re-exports dal's classes).
repositories = graph_repositories

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_GRAPH_STORE = ROOT / 'data' / 'semantic_store'

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'csc501_milestone5_secret')
app.config['BACKEND'] = os.environ.get('ETF_BACKEND', 'graph')  # 'graph' (M5) or 'sql' (M4)
app.config['GRAPH_STORE'] = Path(os.environ.get('ETF_GRAPH_STORE', DEFAULT_GRAPH_STORE))
app.config['GRAPH'] = None     # tests inject a ready GraphDatabase here
app.config['DATABASE'] = DEFAULT_DB_PATH  # M4 mode; tests point this at a temporary copy

FORM_ROWS = 8  # entry rows shown on the create form
DEFAULT_BASIS = 'Synthetic demonstration: all identities and weights are fictional.'


_graph_lock = threading.Lock()


class GraphStoreUnavailable(RuntimeError):
    """The graph store has not been created yet; the message says how to fix it."""


def graph():
    """Return the one shared GraphDatabase for this process.

    The embedded store allows one writable opener per directory, so the graph is
    opened once (ontology loaded, validators attached) and reused by every request.
    """
    with _graph_lock:
        if app.config['GRAPH'] is None:
            from semantic.runtime import open_graph_database
            from semantic.vocabulary import DATA_GRAPH
            store = Path(app.config['GRAPH_STORE'])
            if not store.exists():
                raise GraphStoreUnavailable(f'Graph store not found at {store}. '
                                   'Run: python quickstart_semantic.py')
            try:
                opened = open_graph_database(store)
            except OSError as exc:
                if 'lock' not in str(exc).lower():
                    raise
                raise GraphStoreUnavailable(
                    f'Graph store {store} is already open in another process '
                    '(only one app or quickstart may use it at a time).') from exc
            if not any(q.graph_name == DATA_GRAPH for q in opened.snapshot()):
                raise GraphStoreUnavailable(f'Graph store {store} has no data graph. '
                                   'Run: python quickstart_semantic.py')
            app.config['GRAPH'] = opened
        return app.config['GRAPH']


class Data:
    """The data-access modules plus the handle they take (graph or connection)."""

    def __init__(self, repos, looks, handle):
        self.repos, self.lookups, self.handle = repos, looks, handle


@contextmanager
def data():
    if app.config['BACKEND'] == 'sql':
        with Database(app.config['DATABASE']) as conn:
            yield Data(sql_repositories, sql_lookups, conn)
    elif app.config['BACKEND'] == 'graph':
        yield Data(graph_repositories, graph_lookups, graph())
    else:
        raise RuntimeError(f"Unknown BACKEND {app.config['BACKEND']!r}")


@app.context_processor
def backend_label():
    if app.config['BACKEND'] == 'graph':
        return {'backend_label': 'Knowledge graph (RDF/OWL, SPARQL on Oxigraph)'}
    return {'backend_label': 'Relational (SQLite)'}


def _message(exc):
    if isinstance(exc, GraphStoreUnavailable):
        return str(exc)
    return biz.friendly_error(exc)


def _fail(exc):
    flash(_message(exc), 'error')


def _require_in_snapshot(d, snapshot_id, entry_ids):
    owned = {e['EntryId'] for e in d.repos.get_allocation_entries(d.handle, snapshot_id)}
    if not set(entry_ids) <= owned:
        raise repositories.ValidationError('Some entries do not belong to this disclosure.')


# ---------------------------------------------------------------- search
@app.route('/')
def index():
    filters = {k: request.args.get(k, '') for k in ('ticker', 'dimension', 'as_of')}
    disclosures = []
    try:
        parsed = biz.parse_search(request.args)
        filters['ticker'] = parsed['ticker'] or ''
        with data() as d:
            disclosures = d.repos.search_disclosures(
                d.handle, ticker=parsed['ticker'],
                dimension_name=parsed['dimension'], as_of_date=parsed['as_of'])
    except Exception as exc:
        _fail(exc)
    return render_template('index.html', disclosures=disclosures, filters=filters,
                           dimensions=biz.DIMENSIONS)


# ---------------------------------------------------------------- detail
def _render_detail(snapshot_id, edits=None, status=200):
    with data() as d:
        detail = d.repos.get_disclosure_detail(d.handle, snapshot_id)
        same_etf = d.repos.search_disclosures(d.handle, etf_id=detail['ETFId'])
    match = next((r for r in same_etf if r['SnapshotId'] == snapshot_id), {})
    detail['Ticker'] = match.get('Ticker')
    detail['ExchangeContext'] = match.get('ExchangeContext')
    entries = biz.annotate_entries(detail['Entries'])
    for e in entries:
        e['Input'] = (edits or {}).get(e['EntryId'], e['WeightFraction'])
    return render_template('detail.html', detail=detail, entries=entries,
                           total=biz.total_weight(entries)), status


@app.route('/disclosure/<snapshot_id>')
def detail(snapshot_id):
    try:
        return _render_detail(biz.parse_id(snapshot_id, 'Disclosure'))
    except Exception as exc:
        _fail(exc)
        return redirect(url_for('index'))


# ---------------------------------------------------------------- create
@app.route('/disclosure/new', methods=['GET', 'POST'])
def new_disclosure():
    status = 200
    if request.method == 'POST':
        try:
            payload = biz.parse_new_disclosure(request.form)
            with data() as d:
                created = d.repos.create_disclosure(d.handle, payload)
            flash('Disclosure created.', 'success')
            return redirect(url_for('detail', snapshot_id=created['SnapshotId']))
        except Exception as exc:
            _fail(exc)
            status = 422
    try:
        with data() as d:
            etfs = d.lookups.list_etfs(d.handle)
            dimensions = d.lookups.list_dimensions(d.handle)
            sources = d.lookups.list_source_documents(d.handle)
            categories = d.lookups.list_categories(d.handle)
    except Exception as exc:
        _fail(exc)
        return redirect(url_for('index'))
    rows = (list(zip_longest(request.form.getlist('category'),
                             request.form.getlist('weight'), fillvalue=''))
            if request.method == 'POST' else [])
    rows += [('', '')] * max(0, FORM_ROWS - len(rows))
    return render_template('new.html', etfs=etfs, dimensions=dimensions, sources=sources,
                           categories=biz.category_scopes(categories, sources),
                           statuses=biz.COVERAGE_STATUSES, rows=rows, form=request.form,
                           default_basis=DEFAULT_BASIS), status


# ---------------------------------------------------------------- update / delete
@app.route('/update_weights', methods=['POST'])
def update_weights():
    try:
        snapshot_id = biz.parse_id(request.form.get('snapshot_id'), 'Disclosure')
    except Exception as exc:
        _fail(exc)
        return redirect(url_for('index'))
    try:
        changes = biz.parse_batch(request.form)
        with data() as d:
            _require_in_snapshot(d, snapshot_id, [c['EntryId'] for c in changes])
            d.repos.update_weights_batch(d.handle, changes)
        flash(f'Saved {len(changes)} weight(s) together.', 'success')
        return redirect(url_for('detail', snapshot_id=snapshot_id))
    except Exception as exc:
        _fail(exc)
    try:  # keep what the user typed
        return _render_detail(snapshot_id, biz.submitted_weights(request.form), 422)
    except Exception as exc:
        _fail(exc)
        return redirect(url_for('index'))


@app.route('/delete_entry', methods=['POST'])
def remove_entry():
    snapshot_id = request.form.get('snapshot_id', type=int)
    try:
        entry_id = biz.parse_id(request.form.get('entry_id'), 'Entry')
        with data() as d:
            if snapshot_id:
                _require_in_snapshot(d, snapshot_id, [entry_id])
            d.repos.delete_entry(d.handle, entry_id)
        flash('Entry deleted.', 'success')
    except Exception as exc:
        _fail(exc)
    if snapshot_id:
        return redirect(url_for('detail', snapshot_id=snapshot_id))
    return redirect(url_for('index'))


# ---------------------------------------------------------------- portfolio
@app.route('/portfolio')
def portfolio():
    number = request.args.get('customer', '').strip()
    portfolio_id = request.args.get('portfolio_id', type=int)
    holding_date = request.args.get('holding_date', '').strip() or None
    customers, portfolios, dates, result, disclosures = [], [], [], None, {}
    try:
        if holding_date:
            holding_date = biz.parse_date(holding_date, 'Holding date')
        with data() as d:
            customers = d.lookups.list_customers(d.handle)
            if number:
                portfolios = d.lookups.list_customer_portfolios(d.handle, number)
                if portfolio_id is None and len(portfolios) == 1:
                    portfolio_id = portfolios[0]['PortfolioId']
                if portfolio_id:
                    dates = d.lookups.list_holding_dates(d.handle, portfolio_id)
                    if holding_date is None and len(dates) == 1:
                        holding_date = dates[0]
                try:
                    result = d.repos.get_customer_portfolio(
                        d.handle, number, portfolio_id=portfolio_id,
                        holding_as_of_date=holding_date)
                except repositories.ValidationError as exc:
                    _fail(exc)  # asks the user to choose a portfolio or date
                if result:
                    for h in result['Holdings']:
                        disclosures[h['ETFId']] = d.repos.search_disclosures(
                            d.handle, etf_id=h['ETFId'])
    except Exception as exc:
        _fail(exc)
    return render_template('portfolio.html', customers=customers, portfolios=portfolios,
                           dates=dates, number=number, portfolio_id=portfolio_id,
                           holding_date=holding_date, result=result, disclosures=disclosures)


# ---------------------------------------------------------------- errors
@app.route('/favicon.ico')
def favicon():
    # Browsers request this automatically; answer quietly instead of letting the
    # 404 handler queue a "not available" message onto the user's next page.
    return '', 204


@app.errorhandler(HTTPException)
def handle_http_error(exc):
    flash('That page or action is not available.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    flash(_message(exc), 'error')
    return redirect(url_for('index'))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Run the ETF allocation web UI.')
    parser.add_argument('--backend', choices=('graph', 'sql'), default=app.config['BACKEND'])
    parser.add_argument('--store', type=Path, default=app.config['GRAPH_STORE'],
                        help='graph store directory (created by quickstart_semantic.py)')
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', type=int, default=5000)
    args = parser.parse_args(argv)
    app.config['BACKEND'] = args.backend
    app.config['GRAPH_STORE'] = args.store
    if args.backend == 'graph':
        try:
            graph()  # fail fast with a clear message if the store is missing
        except GraphStoreUnavailable as exc:
            raise SystemExit(str(exc))
    # One process and no reloader: the embedded store has a single writable opener.
    app.run(host=args.host, port=args.port, debug=False, use_reloader=False, threaded=True)


if __name__ == '__main__':
    main()
