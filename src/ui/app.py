"""Flask interface for the ETF allocation demonstration (Shahmeer).

Layers: routes (this file) -> business logic (src/biz) -> data access (src/dal).
This module contains no SQL. It reads request data, calls biz/DAL functions,
and turns results or errors into pages and flashed messages.
"""
import os
import sys
from itertools import zip_longest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, flash, redirect, render_template, request, url_for
from werkzeug.exceptions import HTTPException

from biz import disclosures as biz
from dal import lookups, repositories
from dal.database import DEFAULT_DB_PATH, Database

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'csc501_milestone4_secret')
app.config['DATABASE'] = DEFAULT_DB_PATH  # tests point this at a temporary copy

FORM_ROWS = 8  # entry rows shown on the create form
DEFAULT_BASIS = 'Synthetic demonstration: all identities and weights are fictional.'


def db():
    return Database(app.config['DATABASE'])


def _fail(exc):
    flash(biz.friendly_error(exc), 'error')


def _require_in_snapshot(conn, snapshot_id, entry_ids):
    owned = {e['EntryId'] for e in repositories.get_allocation_entries(conn, snapshot_id)}
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
        with db() as conn:
            disclosures = repositories.search_disclosures(
                conn, ticker=parsed['ticker'],
                dimension_name=parsed['dimension'], as_of_date=parsed['as_of'])
    except Exception as exc:
        _fail(exc)
    return render_template('index.html', disclosures=disclosures, filters=filters,
                           dimensions=biz.DIMENSIONS)


# ---------------------------------------------------------------- detail
def _render_detail(snapshot_id, edits=None, status=200):
    with db() as conn:
        detail = repositories.get_disclosure_detail(conn, snapshot_id)
        same_etf = repositories.search_disclosures(conn, etf_id=detail['ETFId'])
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
            with db() as conn:
                created = repositories.create_disclosure(conn, payload)
            flash('Disclosure created.', 'success')
            return redirect(url_for('detail', snapshot_id=created['SnapshotId']))
        except Exception as exc:
            _fail(exc)
            status = 422
    try:
        with db() as conn:
            etfs = lookups.list_etfs(conn)
            dimensions = lookups.list_dimensions(conn)
            sources = lookups.list_source_documents(conn)
            categories = lookups.list_categories(conn)
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
        with db() as conn:
            _require_in_snapshot(conn, snapshot_id, [c['EntryId'] for c in changes])
            repositories.update_weights_batch(conn, changes)
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
        with db() as conn:
            if snapshot_id:
                _require_in_snapshot(conn, snapshot_id, [entry_id])
            repositories.delete_entry(conn, entry_id)
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
        with db() as conn:
            customers = lookups.list_customers(conn)
            if number:
                portfolios = lookups.list_customer_portfolios(conn, number)
                if portfolio_id is None and len(portfolios) == 1:
                    portfolio_id = portfolios[0]['PortfolioId']
                if portfolio_id:
                    dates = lookups.list_holding_dates(conn, portfolio_id)
                    if holding_date is None and len(dates) == 1:
                        holding_date = dates[0]
                try:
                    result = repositories.get_customer_portfolio(
                        conn, number, portfolio_id=portfolio_id,
                        holding_as_of_date=holding_date)
                except repositories.ValidationError as exc:
                    _fail(exc)  # asks the user to choose a portfolio or date
                if result:
                    for h in result['Holdings']:
                        disclosures[h['ETFId']] = repositories.search_disclosures(conn, etf_id=h['ETFId'])
    except Exception as exc:
        _fail(exc)
    return render_template('portfolio.html', customers=customers, portfolios=portfolios,
                           dates=dates, number=number, portfolio_id=portfolio_id,
                           holding_date=holding_date, result=result, disclosures=disclosures)


# ---------------------------------------------------------------- errors
@app.errorhandler(HTTPException)
def handle_http_error(exc):
    flash('That page or action is not available.', 'error')
    return redirect(url_for('index'))


@app.errorhandler(Exception)
def handle_unexpected_error(exc):
    flash(biz.friendly_error(exc), 'error')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
