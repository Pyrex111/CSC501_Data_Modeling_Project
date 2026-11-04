import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import Flask, render_template, request, flash, redirect, url_for
from dal.database import Database
from dal import repositories

app = Flask(__name__)
app.secret_key = 'csc501_milestone4_secret'

@app.route('/', methods=['GET', 'POST'])
def index():
    ticker = request.form.get('ticker') if request.method == 'POST' else None
    with Database() as conn:
        disclosures = repositories.search_disclosures(conn, ticker=ticker)
    return render_template('index.html', disclosures=disclosures, search_term=ticker)

@app.route('/disclosure/<int:snapshot_id>')
def detail(snapshot_id):
    try:
        with Database() as conn:
            detail = repositories.get_disclosure_detail(conn, snapshot_id)
            entries = repositories.get_allocation_entries(conn, snapshot_id)
        return render_template('detail.html', detail=detail, entries=entries)
    except Exception as e:
        flash(f"Error loading disclosure: {str(e)}", "error")
        return redirect(url_for('index'))

@app.route('/update_weight', methods=['POST'])
def update_weight():
    entry_id = request.form.get('entry_id', type=int)
    new_weight = request.form.get('weight', type=float)
    snapshot_id = request.form.get('snapshot_id', type=int)
    
    try:
        with Database() as conn:
            repositories.update_entry_weight(conn, entry_id, new_weight)
        flash("Weight updated successfully.", "success")
    except Exception as e:
        flash(f"Update failed: {str(e)}", "error")
        
    return redirect(url_for('detail', snapshot_id=snapshot_id))

if __name__ == '__main__':
    app.run(debug=True)