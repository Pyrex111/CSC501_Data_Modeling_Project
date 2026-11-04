# Shahmeer: Milestone 4 interface and business logic

Prepared 4 November 2026. Responsibility: the Flask application, its templates, the business-logic layer, and connecting them to Mason's data-access layer (DAL). This is an AI-assisted contribution owned by Shahmeer.

## Deliverables

- [Flask application](../../../../src/ui/app.py): routes only, no SQL.
- [Templates](../../../../src/ui/templates/): `base.html`, `index.html` (search), `detail.html`, `new.html` (create), `portfolio.html`.
- [Business logic](../../../../src/biz/disclosures.py): parsing and validation of form input, the create-disclosure payload, category scoping for the create form, and translation of database/rule errors into plain messages.
- [Lookup queries](../../../../src/dal/lookups.py): read-only, parameterized queries that fill the form controls (ETFs, dimensions, source documents, categories, customers, portfolios). Added to the DAL so the UI writes no SQL. Mason should review it.
- Uses `search_disclosures`, `get_disclosure_detail`, `create_disclosure`, `update_entry_weight`, `delete_entry` and `get_customer_portfolio` from [repositories.py](../../../../src/dal/repositories.py) unchanged.

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
| Update / delete entry | `/update_weight`, `/delete_entry` (POST) | Save one change, flash the result, return to the detail page. |
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

## Observed behavior

These checks were run with Flask's test client against the freshly seeded demo database. They are manual checks of the interface, not an automated suite. The 44 existing tests cover the schema and DAL and still pass.

| Action | Observed result |
| --- | --- |
| Search `sya` (lowercase) | Finds SYA's 2 disclosures. |
| Filter Geography / as-of 2026-06-30 | 3 and 2 disclosures respectively. |
| Open `/disclosure/2` | Heading shows SYA; source, locator and category meanings displayed. |
| Create a Partial sector disclosure (3 entries) | Saved; detail page opens. |
| Create with a duplicate category, no entries, weight 2, bad date, or missing locator | Rejected with a specific message. |
| Create a Complete disclosure totalling 0.8 | Rejected: total would be 0.8. |
| Create a Complete sector disclosure of five 0.2 entries | Saved. |
| Create a Geography disclosure with the matching source and locator | Saved. |
| Same geography categories with a different locator | Rejected: category does not belong to this source and locator. |
| Sector category in a Geography disclosure | Rejected. |
| Update an entry by +0.002 in a Complete disclosure | Saved. |
| Update by +0.04 | Rejected: total would be 1.04. |
| Delete an entry from a Complete disclosure | Rejected: total would be 0.69. |
| Update and delete entries in a Partial disclosure | Saved. |
| Delete the last entry | Rejected: a disclosure must keep at least one entry. |
| Portfolio for customer 1001 | Holdings at 2026-08-01 with dated disclosures per ETF. |
| Unknown customer, unknown disclosure | "not found" message, page stays valid. |

## Known limitations

- A Complete disclosure must always total 1 ± 0.005, so single-entry updates and deletes in Complete disclosures only work for very small changes. Larger rebalancing needs several weights changed together; `update_weights_batch` exists in the DAL but the interface does not expose it. Entry deletion is demonstrated on Partial disclosures.
- The interface cannot create new ETFs, source documents or categories; it only uses existing ones. The DAL has no functions for these.
- Geography categories are tied to one source document and locator, so a new geography disclosure must reuse a source and locator that already have categories.
- There is no CSRF protection, authentication or automated UI test suite. The secret key defaults to a fixed development value.
- Screenshots in the final report were taken by the team from the running application; none are stored in the repository by this contribution.

## Handoff boundaries

The templates depend on the field names returned by `repositories.py` and `lookups.py`. If Mason renames a returned column, the matching template field must change too. The architecture figure should show the order UI, business logic, DAL, then `validated_transaction` (called from the DAL), and should list only the operations above.

## AI-use and evaluation record

AI assisted with reviewing the interface against the manual and the team handoff, writing the business-logic and lookup modules, the new templates and routes, running the manual checks listed above, and drafting this README. The checks were run by the assistant with Flask's test client; they do not claim that Shahmeer personally ran them or tested the pages in a browser. The manual permits AI task completion with human evaluation; Shahmeer and the team must review and run the interface and disclose the assistance in the final submission. Mason's and Taimoor's approval of the interface and of `lookups.py` is not asserted.
