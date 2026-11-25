# Backend and ontology integration — 24 November 2026

Taimoor's backend integration against Mason's handoff commit
`eaa23eff266792b985d2b0cc3e1d0007041643fd`. AI implemented and executed the
checks below; this is not a claim that a student personally ran them.

## Changes

- `semantic.runtime.open_graph_database` is the shared startup for the quickstart,
  CRUD demo and future graph-connected UI. It attaches Mason's
  `make_backend_validator(capture_root=ROOT)` and retains the accepted M4 parity
  bridge. It validates an existing ABox before replacing the ontology named graph.
- Startup loads the committed `etf_allocations.owl` by default. The existing
  `--ontology` option can select another RDF/XML file, without asserting that a
  custom ontology has matching terms. No OWL reasoner is enabled.
- Quickstart evidence reports the active validation layers and ontology triple
  count. Reusing a valid store preserves its data. A missing ontology is rejected
  before creating a persistent store directory.
- The CRUD demo uses the same integrated startup. The graph repository signatures,
  six SPARQL query files, ontology axioms and Mason's validator are unchanged.

## Verification actually executed

| Check | Result |
| --- | --- |
| Baseline before edits | 151 tests passed |
| Full suite after integration | 160 tests passed: 74 M4, 26 backend, 51 ontology, nine runtime |
| Fresh persistent quickstart and subsequent reuse | Passed with the default ontology and both validators |
| All six SQL/SPARQL result multisets | Equal; row counts 8, 2, 5, 5, 5, 17 |
| ABox exported and checked by Mason's CLI | 356 triples, zero issues |
| Repository create, batch update and partial entry deletion | Saved with the native callback invoked |
| Invalid Complete edit/deletion and final-entry deletion | Rejected; complete dataset unchanged |
| Native-only checks with SQL bridge bypassed inside tests | Bad totals, edit/deletion, final entry and missing capture rejected |
| Existing invalid persistent data | Startup rejected; existing dataset unchanged |

The runtime tests exercise the real native validator rather than a stub; only the
legacy SQL checker is mocked in tests designed to isolate native enforcement.
The ordinary application path always retains both validation layers.

Machine-readable output: [backend_integration_verification.json](backend_integration_verification.json).
The earlier `verification.json` is retained as a dated initial-backend record.

## Reproduce

```sh
python -m pip install -r requirements-semantic.txt
python quickstart_semantic.py --store data/semantic_store --compare
python scripts/demo_semantic_crud.py
python -m unittest discover -s tests -q
```

For baseline comparisons after editing a store, choose a new temporary store path
and export path; do not reset user data to make `--compare` pass. Checks ran on
Linux/Python 3.12. Windows/macOS application behavior is not asserted.

## Handoff to Shahmeer

Make `src` importable, then initialize once at application startup:

```python
from semantic.runtime import open_graph_database
from semantic import repositories, lookups

graph = open_graph_database('data/semantic_store')
rows = repositories.search_disclosures(graph, ticker='SYA')
```

Run the quickstart first to seed the persistent data graph. Pass this same shared
`graph` to the documented repositories and lookup functions, instead of passing a
SQLite connection. The factory loads the ontology and checks existing data; it
does not seed data or start Flask. Do not open a writable store per request, use
multiple worker processes, or run a debug reloader with independent writable
instances. Do not modify the private store directly.

The SQLite-backed Flask application has not been changed by this work. Its graph
adaptation, end-to-end UI checks, screenshots, architecture and the assembled
three-page report/package remain team integration work. Native validation
integration does not resolve the previously documented external IRI reuse limits
or enable OWL inference.
