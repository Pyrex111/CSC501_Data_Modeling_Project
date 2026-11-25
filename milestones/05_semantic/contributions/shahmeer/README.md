# Shahmeer: Milestone 5 graph-backed interface

Prepared 25 November 2026, on top of `milestone5/taimoor-semantic-backend` at
`4f09d50`. Responsibility: connecting the Flask UI to the knowledge graph
(manual 5.4), UI tests, screenshots, the M5 architecture figure and the UI
report section. This is an AI-assisted contribution owned by Shahmeer.

## What changed

| File | Change |
| --- | --- |
| [src/ui/app.py](../../../../src/ui/app.py) | Routes now use `semantic.repositories` / `semantic.lookups` with one shared graph from `semantic.runtime.open_graph_database()`. The M4 SQLite layer stays selectable with `BACKEND='sql'` (or `--backend sql`) for regression only. Added a CLI (`--store`, `--port`), a clear message when the graph store is missing, and a quiet `/favicon.ico` route. |
| [src/ui/templates/base.html](../../../../src/ui/templates/base.html) | Banner shows the active data source ("Knowledge graph (RDF/OWL, SPARQL on Oxigraph)"). |
| [src/biz/disclosures.py](../../../../src/biz/disclosures.py) | `friendly_error` also translates graph-validator messages: duplicate snapshot, category/snapshot dimension mismatch, unknown referenced record. |
| [quickstart_semantic.py](../../../../quickstart_semantic.py) | New `--serve` (and `--port`) flag: after setup, starts the UI on the same graph instance. |
| [tests/test_ui_routes.py](../../../../tests/test_ui_routes.py) | State checks moved into small helper methods; tests and assertions otherwise unchanged and still run on SQLite. |
| [tests/test_ui_graph_routes.py](../../../../tests/test_ui_graph_routes.py) | New. Reruns all 26 route tests against a fresh, validated in-memory graph opened through the real startup path, plus 3 graph-specific tests. "Unchanged" means the full quad set (ontology + data) is identical. |
| [scripts/capture_ui_screenshots.py](../../../../scripts/capture_ui_screenshots.py) | New. Builds a throwaway graph, serves the UI and recaptures all screenshots with a headless browser; asserts the graph is unchanged after each rejected write. |
| [figures/system_architecture_m5.dot](../../figures/system_architecture_m5.dot) | New architecture figure (PDF/PNG rendered alongside). |
| [report/shahmeer_ui_semantic_section.tex](../../report/shahmeer_ui_semantic_section.tex) | UI section for the team report. |

## How to run

From the repository root:

```sh
python -m pip install -r requirements-semantic.txt
python quickstart_semantic.py --serve        # build/reuse graph, then open http://127.0.0.1:5000/
# or, if the graph already exists:
python src/ui/app.py                         # --store data/semantic_store --port 5000
```

Run one process only. The embedded store accepts one writable opener, so the
app runs without the debug reloader. Stop the app before running
`quickstart_semantic.py` again against the same store.

## Manual 5.4 coverage

| Requirement | Page | Graph operation |
| --- | --- | --- |
| Data entry | New disclosure (`/disclosure/new`) | `create_disclosure` → validated `INSERT DATA` |
| Data retrieval | Search (`/`), detail, portfolio | SPARQL `SELECT` through `search_disclosures`, `get_disclosure_detail`, `get_customer_portfolio` and lookups |
| Update | Save all weights (`/update_weights`) | `update_weights_batch` → one `DELETE DATA`/`INSERT DATA` delta |
| Delete | Delete button (`/delete_entry`) | `delete_entry` → validated `DELETE DATA` |

## Evidence

- `python -m unittest discover -s tests` → **189 tests OK**: the 160 tests from the
  previous handoff, 26 route tests rerun on the graph and 3 graph-specific tests.
- `python quickstart_semantic.py --compare` → all six SPARQL results still match SQL
  (8, 2, 5, 5, 5, 17 rows); `demo.rdf` unchanged.
- [Screenshots](../../docs/screenshots/) 01–11, from `scripts/capture_ui_screenshots.py`:

| # | Shows |
| --- | --- |
| 01–02 | Search, all disclosures and filtered (ticker `sya` normalized, Sector) |
| 03 | Disclosure detail with provenance and classification |
| 04–05 | Create form filled, then saved (Partial, total 0.8) |
| 06 | Same create repeated → "That record already exists" |
| 07 | Batch update saved (0.45 / 0.25 / 0.1) |
| 08 | Complete disclosure edited to total 1.04 → rejected, input kept |
| 09 | Entry deleted from the Partial disclosure (total 0.7) |
| 10 | Delete that would make a Complete total 0.585 → rejected |
| 11 | Portfolio with holding date and separately dated disclosures |

## Findings while integrating

- On the graph, two rejections came back as raw parity-bridge text
  (`UNIQUE constraint failed: ...`, `Category and snapshot dimensions must agree`) and
  one as `... has missing/wrong-class target`. The M4 SQLite path produced friendly
  messages for the same cases, so the translation rules were extended. Without the
  graph copy of the route tests these would have reached users as raw text.
- The parity bridge runs first, so for these cases Mason's native validator is not
  the check that rejects them in the UI. Native-only rejection is covered by
  Taimoor's runtime tests.
- Browsers request `/favicon.ico` automatically. In M4 that hit the 404 handler and
  put "That page or action is not available" on the user's next page. That bug was
  fixed here.
- The ontology graph is not read on writes; validation rules are restated in code
  (see Mason's `--rules`). The architecture figure says so.

## AI use

AI (Claude) wrote the route and test changes, screenshot script, figure and report
draft, and ran the recorded checks. Shahmeer must review the diff, run the app and
confirm the screenshots before submission. The manual requires critical evaluation
and citation of AI-generated content.
