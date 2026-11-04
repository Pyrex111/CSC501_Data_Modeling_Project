# Shahmeer: Milestone 4 interface and business logic

Prepared 4 November 2026. Responsibility: the Flask application, its templates, the business-logic layer, route tests, screenshots, and connecting them to Mason's data-access layer (DAL). This is an AI-assisted contribution owned by Shahmeer.

## Deliverables

- [Flask application](../../../../src/ui/app.py): routes only, no SQL.
- [Templates](../../../../src/ui/templates/): `base.html`, `index.html` (search), `detail.html`, `new.html` (create), `portfolio.html`.
- [Business logic](../../../../src/biz/disclosures.py): parsing and validation of form input, the create-disclosure payload, category scoping for the create form, and translation of database/rule errors into plain messages.
- [Lookup queries](../../../../src/dal/lookups.py): read-only, parameterized queries that fill the form controls (ETFs, dimensions, source documents, categories, customers, portfolios). Added to the DAL so the UI writes no SQL. Mason should review it.
- [Route and business-logic tests](../../../../tests/test_ui_routes.py): 30 tests against a temporary copy of the synthetic database.
- [Screenshots](../../figures/ui_screenshots/): nine captures of the running application showing each operation and its result.
- [Report section](../../report/shahmeer_ui_section.tex): about 190 words of LaTeX for the interface, validation and results.
- Uses `search_disclosures`, `get_disclosure_detail`, `create_disclosure`, `update_weights_batch`, `delete_entry` and `get_customer_portfolio` from [repositories.py](../../../../src/dal/repositories.py) unchanged.

## How to run

From the repository root, with `pip install -r requirements.txt`:

```sh
python quickstart.py --serve
```

The app starts on `http://127.0.0.1:5000/`. Optional environment variables: `FLASK_SECRET_KEY` (session key) and `FLASK_DEBUG=1` (debug mode, off by default).

## What the interface does

| Page | Route | Operation |
| --- | --- | --- |
| Search disclosures | `/` | Search by ticker (case-insensitive), dimension and as-of date. |
| Disclosure detail | `/disclosure/<id>` | View ETF, provider, dimension, as-of date, coverage, basis note, source URL, locator, retrieval and publication dates, retained capture, each category's meaning, and the weight total. Update or delete each entry. |
| New disclosure | `/disclosure/new` | Create a snapshot with its entries in one transaction. |
| Update weights | `/update_weights` (POST) | Save all edited weights of a disclosure in one transaction (`update_weights_batch`). On failure the page is redisplayed with the typed values. |
| Delete entry | `/delete_entry` (POST) | Delete one entry; rejected if it would break a Complete total or remove the last entry. |
| Portfolio | `/portfolio` | Show a customer's portfolio at one holding date, next to the separately dated disclosures available for each held ETF. |

## Layers

Routes (`src/ui`) call business logic (`src/biz`), which validates input and calls the DAL (`src/dal`). The DAL runs every write inside `validated_transaction`, which checks the final database state before committing. Each request opens its own connection with `with Database() as conn`.

## Input validation

- **Browser:** number inputs have `min`, `max` and `step`; required fields are marked; the create form shows only the categories that fit the chosen dimension, source document and locator, and a running total.
- **Business layer:** ids must be integers; dates must be real `YYYY-MM-DD` dates; weights must be finite fractions from 0 to 1; locator and basis note are required; coverage must be Complete, Partial or Unknown; a new disclosure needs at least one entry, each with a category and a weight, and no category twice; tickers are trimmed and uppercased.
- **DAL and database:** weights are range-checked again, all SQL is parameterized, and `CHECK` constraints and triggers apply. `validated_transaction` rejects any change that leaves a Complete disclosure outside 1 ± 0.005, leaves a disclosure without entries, or uses a category that does not belong to the disclosure's source and dimension.

Jinja2 autoescaping is on for the `.html` templates.

## Exception handling

Routes catch every error and show it through `friendly_error`, which turns repository, rule and `sqlite3` errors into plain messages (for example, "A Complete disclosure must add up to 1 (allowed error 0.005). This change would make the total 1.04."). The user stays on a valid page and no partial data is saved.



## Checks performed

- **Automated:** `python -m unittest discover -s tests` ran 74 tests, all passing: the 44 schema/DAL tests plus 30 new ones in `tests/test_ui_routes.py`. The new tests use Flask's test client against a temporary copy of the synthetic database. They cover search filters and ticker normalization, the detail page's preserved information, creation (Partial, Complete, Geography), 15 rejected creates, coherent and incoherent batch updates, 9 invalid update inputs, delete in Complete and Partial disclosures, the last-entry rule, portfolio selection, and malformed ids, dates and URLs. Every rejected write is checked to leave a full database dump unchanged. They do not drive a browser or check page appearance.
- **Running application:** the real server was started with `python src/ui/app.py` and driven with HTTP requests through search, detail, portfolio, create, rejected create, rejected and saved batch updates, rejected delete and successful delete. The pages were rendered to the screenshots listed below with wkhtmltoimage.
- **Clean checkout:** from a fresh unzip of the repository with this contribution copied in, `python quickstart.py --serve` built the database, started the application, and `/`, `/portfolio` and `/disclosure/new` returned 200. The 74 tests passed there too.



## Screenshots

Stored in `milestones/04_relational/figures/ui_screenshots/`. Each shows the result page, including its message.

| File | Shows |
| --- | --- |
| `01_search_geography_filter` | Search filtered to the Geography dimension |
| `02_detail_with_source_and_classification` | Disclosure detail with basis, source, locator, retained file and classification |
| `03_portfolio_holding_vs_allocation_dates` | Portfolio with the holding date apart from allocation dates |
| `04_create_partial_disclosure_saved` | Newly created Partial synthetic disclosure |
| `05_create_rejected_total_form_kept` | Complete disclosure totalling 0.8 rejected, entered values kept |
| `06_update_rejected_total_1.04` | Edit rejected: total would be 1.04, typed values kept |
| `07_update_batch_saved` | Coherent multi-entry update saved |
| `08_delete_rejected_complete` | Delete from a Complete disclosure rejected |
| `09_delete_saved_partial` | Entry deleted from the Partial disclosure |

These were captured from rendered pages, not from a desktop browser. Retake them in a browser if the team wants browser chrome visible.

## Known limitations

- A Complete disclosure must total 1 within 0.005, so changes must be coherent and deleting an entry from one is normally rejected. Deletion is demonstrated on a Partial synthetic disclosure created through the create form; no Complete disclosure's status was changed.
- The interface cannot create ETFs, source documents or categories; the DAL has no functions for them.
- Geography categories are tied to one source document and locator, so a new geography disclosure must reuse a source and locator that already have categories.
- There is no CSRF protection or authentication. The secret key defaults to a fixed development value; set `FLASK_SECRET_KEY` to override it. Debug mode is off unless `FLASK_DEBUG=1`.
- Entry lists are ordered by the DAL (largest weight first), so rows can move after an edit.

## Handoff boundaries

The templates depend on the field names returned by `repositories.py` and `lookups.py`. If Mason renames a returned column, the matching template field must change too. The architecture figure should show the order UI, business logic, DAL, then `validated_transaction` (called from the DAL), and should list only the operations above.

## AI-use and evaluation record

AI assisted with reviewing the interface against the manual and the team's feedback, writing the business-logic and lookup modules, the routes and templates, the route tests, drafting this README and the report section, and rendering the screenshots. The checks above were run by the assistant; they do not claim that Shahmeer personally ran them or used the pages in a desktop browser. The manual permits AI task completion with human evaluation; Shahmeer and the team must review and run the interface and disclose the assistance in the final submission. Mason's and Taimoor's approval of the interface and of `lookups.py` is not asserted.
