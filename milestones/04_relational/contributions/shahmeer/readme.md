# Shahmeer: Milestone 4 Flask interface

Prepared 4 November 2026. Responsibility: the Flask application (`app.py`), the two Jinja2 templates, and connecting them to Mason's data-access layer (DAL). This is an AI-assisted contribution owned by Shahmeer.

## Deliverables

- [Flask application](../../../../src/ui/app.py): three routes (search, detail, update) that call the DAL and contain no SQL.
- [Search page](../../../../src/ui/templates/index.html): ticker search form and a table of disclosures with a link to each.
- [Detail page](../../../../src/ui/templates/detail.html): disclosure header, allocation entries, and one update form per entry.
- Integration with the DAL: `Database` connection manager and the `search_disclosures`, `get_disclosure_detail`, `get_allocation_entries` and `update_entry_weight` functions in [repositories.py](../../../../src/dal/repositories.py).
- Launch path: `python quickstart.py --serve` builds or validates the demo database, then starts `src/ui/app.py`.

## How to run

From the repository root, with Flask installed (`pip install -r requirements.txt`):

```sh
python quickstart.py --serve
```

The app starts on `http://127.0.0.1:5000/`. It reads `data/etf_allocations.sqlite3`, which `quickstart.py` creates from the synthetic seed if it is missing.

## How the interface works

| Route | Methods | What it does |
| --- | --- | --- |
| `/` | GET, POST | Lists disclosures. A ticker submitted from the form is passed to `search_disclosures`; with no ticker, all disclosures are shown. |
| `/disclosure/<int:snapshot_id>` | GET | Loads one snapshot with `get_disclosure_detail` and its entries with `get_allocation_entries`, then renders the detail page. |
| `/update_weight` | POST | Reads `entry_id`, `snapshot_id` and `weight`, calls `update_entry_weight`, flashes the outcome, and redirects back to the detail page. |

1. **No SQL in the UI.** Every query and write is a call into `repositories.py`. The UI never touches `sqlite3` directly.
2. **One connection per request.** Each route uses `with Database() as conn`, so the connection is always closed and an open transaction is rolled back if an error escapes.
3. **Post/Redirect/Get.** The update route redirects after writing, so refreshing the page cannot resubmit the change.
4. **Errors are shown, not thrown.** Failures are caught in the routes and displayed as flashed messages, so the user sees the reason instead of a server error page.

## Input validation

Validation is layered, and the later layers do not rely on the earlier ones.

- **Browser:** the weight field is a `number` input with `step="0.001"` and `required`.
- **Flask:** `<int:snapshot_id>` rejects non-integer URLs. Form values are read with `type=int` / `type=float`, so a malformed value becomes `None` instead of raising.
- **DAL:** `_validate_weight` rejects a missing or non-numeric weight and any value outside 0 to 1. `update_entry_weight` checks that the entry exists. All SQL is parameterized.
- **Database:** `CHECK (WeightFraction BETWEEN 0.0 AND 1.0)`, plus Taimoor's `validated_transaction`, which rolls back any write that leaves a `Complete` snapshot outside 1 ± 0.005.

Jinja2 autoescaping is active for `.html` templates, so displayed fund names and labels cannot inject markup.

## Exception handling

The DAL raises `ValidationError`, `NotFoundError` and `BusinessRuleError`. The routes catch them and flash the message.

- Detail route: any failure while loading flashes `Error loading disclosure: ...` and redirects to the search page. A nonexistent snapshot gives `Disclosure 999 not found.`
- Update route: success flashes `Weight updated successfully.` Failure flashes `Update failed: <reason>` and returns to the same detail page.

## Observed behavior

The checks below were run with Flask's test client against the seeded demo database. They are manual checks of the interface, not an automated test suite. The 44 existing tests cover the schema and DAL, not the UI.

| Action | Observed result |
| --- | --- |
| Open `/` | Page loads and lists the seeded disclosures. |
| Search for `SYA` | Returns that ETF's disclosures only. |
| Open `/disclosure/2` | Detail page loads with its entries. |
| Set SYA's first sector weight from 0.310 to 0.312 | `Weight updated successfully.` |
| Set the same weight to 0.35 | `Update failed: AllocationSnapshot 2: complete total is 1.04, expected 1`; database unchanged. |
| Submit a non-numeric weight directly | `Update failed: Weight is required.` |
| Open `/disclosure/999` | Redirect to `/` with `Disclosure 999 not found.` |

## Known limitations

- **Single-entry edits.** The form updates one weight at a time, but a `Complete` snapshot must stay within 1 ± 0.005. Only very small single-entry changes are accepted. `update_weights_batch` exists in the DAL for multi-row changes, but the interface does not use it yet.
- **Detail heading.** The detail page heading reads "Disclosure Details for" with no ticker, because `get_disclosure_detail` does not return a `Ticker` field that `detail.html` expects.
- **Error wording.** A non-numeric weight sent directly to the server reports "Weight is required." because `type=float` converts it to `None` before the DAL sees it.
- **Search.** Ticker search is an exact, case-sensitive match on the stored uppercase identifier, so `sya` finds nothing.
- **Prototype settings.** `app.secret_key` is a fixed development value and the app runs with `debug=True`. Neither is suitable for deployment.
- **Scope.** The interface supports search, view and single-weight update only. It does not create disclosures or delete entries, although the DAL supports both.

## Handoff boundaries

The interface depends on the DAL signatures and the column names returned by `repositories.py` (`SnapshotId`, `Ticker`, `FundName`, `DimensionName`, `AllocationAsOfDate`, `EntryId`, `Label`, `WeightFraction`). If Mason renames a returned column, the matching template field must change too. The final report sections on the interface, input validation and exception handling are based on this behavior.

## AI-use and evaluation record

AI assisted with explaining the code, reviewing the interface against the DAL and schema, running the manual checks listed above, and drafting this README and the report text on the interface, input validation and exception handling. The checks were run by the assistant with Flask's test client; they do not claim that Shahmeer personally ran them or tested the pages in a browser. The manual permits AI task completion with human evaluation; Shahmeer and the team must review the interface and disclose the assistance in the final submission. Mason's and Taimoor's approval of the interface is not asserted.