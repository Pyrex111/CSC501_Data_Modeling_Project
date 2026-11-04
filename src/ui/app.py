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

from biz import disclosures as biz
from dal import lookups, repositories
from dal.database import Database

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'csc501_milestone4_secret')

FORM_ROWS = 8  # entry rows shown on the create form


def _fail(exc):
    flash(biz.friendly_error(exc), 'error')


@app.route('/')
def index():
    filters = {k: request.args.get(k, '') for k in ('ticker', 'dimension', 'as_of')}
    disclosures = []
    try:
        parsed = biz.parse_search(request.args)
        with Database() as conn:
            disclosures = repositories.search_disclosures(
                conn, ticker=parsed['ticker'],
                dimension_name=parsed['dimension'], as_of_date=parsed['as_of'])
    except Exception as exc:
        _fail(exc)
    return render_template('index.html', disclosures=disclosures, filters=filters,
                           dimensions=biz.DIMENSIONS)


@app.route('/disclosure/<int:snapshot_id>')
def detail(snapshot_id):
    try:
        with Database() as conn:
            detail = repositories.get_disclosure_detail(conn, snapshot_id)
            same_etf = repositories.search_disclosures(conn, etf_id=detail['ETFId'])
        match = next((r for r in same_etf if r['SnapshotId'] == snapshot_id), {})
        detail['Ticker'] = match.get('Ticker')
        detail['ExchangeContext'] = match.get('ExchangeContext')
        entries = biz.annotate_entries(detail['Entries'])
        return render_template('detail.html', detail=detail, entries=entries,
                               total=biz.total_weight(entries))
    except Exception as exc:
        _fail(exc)
        return redirect(url_for('index'))


@app.route('/disclosure/new', methods=['GET', 'POST'])
def new_disclosure():
    if request.method == 'POST':
        try:
            payload = biz.parse_new_disclosure(request.form)
            with Database() as conn:
                created = repositories.create_disclosure(conn, payload)
            flash('Disclosure created.', 'success')
            return redirect(url_for('detail', snapshot_id=created['SnapshotId']))
        except Exception as exc:
            _fail(exc)
    try:
        with Database() as conn:
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
                           statuses=biz.COVERAGE_STATUSES, rows=rows, form=request.form)


def _back_to_detail(snapshot_id):
    if snapshot_id:
        return redirect(url_for('detail', snapshot_id=snapshot_id))
    return redirect(url_for('index'))


@app.route('/update_weight', methods=['POST'])
def update_weight():
    snapshot_id = request.form.get('snapshot_id', type=int)
    try:
        entry_id = biz.parse_id(request.form.get('entry_id'), 'Entry')
        weight = biz.parse_weight(request.form.get('weight'))
        with Database() as conn:
            result = repositories.update_entry_weight(conn, entry_id, weight)
        flash(f"Updated {result['Label']} to {result['WeightFraction']}.", 'success')
    except Exception as exc:
        _fail(exc)
    return _back_to_detail(snapshot_id)


@app.route('/delete_entry', methods=['POST'])
def remove_entry():
    snapshot_id = request.form.get('snapshot_id', type=int)
    try:
        entry_id = biz.parse_id(request.form.get('entry_id'), 'Entry')
        with Database() as conn:
            repositories.delete_entry(conn, entry_id)
        flash('Entry deleted.', 'success')
    except Exception as exc:
        _fail(exc)
    return _back_to_detail(snapshot_id)


@app.route('/portfolio')
def portfolio():
    number = request.args.get('customer', '').strip()
    portfolio_id = request.args.get('portfolio_id', type=int)
    holding_date = request.args.get('holding_date', '').strip() or None
    customers, portfolios, dates, result, disclosures = [], [], [], None, {}
    try:
        with Database() as conn:
            customers = lookups.list_customers(conn)
            if number:
                portfolios = lookups.list_customer_portfolios(conn, number)
                chosen = portfolio_id or (portfolios[0]['PortfolioId'] if len(portfolios) == 1 else None)
                if chosen:
                    dates = lookups.list_holding_dates(conn, chosen)
                try:
                    result = repositories.get_customer_portfolio(
                        conn, number, portfolio_id=portfolio_id,
                        holding_as_of_date=holding_date)
                except repositories.ValidationError as exc:
                    _fail(exc)  # ask the user to choose a portfolio or date
                if result:
                    for h in result['Holdings']:
                        disclosures[h['ETFId']] = repositories.search_disclosures(conn, etf_id=h['ETFId'])
    except Exception as exc:
        _fail(exc)
    return render_template('portfolio.html', customers=customers, portfolios=portfolios,
                           dates=dates, number=number, portfolio_id=portfolio_id,
                           holding_date=holding_date, result=result, disclosures=disclosures)


if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')
