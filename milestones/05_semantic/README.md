# Milestone 5: Semantic Web implementation

Initial Taimoor contribution, 20 November 2026; backend integration, 24 November.
Baseline: accepted M4 main
`a00c0052289bc5acce17ad1b57f4d84832abda14`. The official **5_Semantic_Manual.pdf**
controls requirements. The supplied **Milestone-5-CSC501.pdf** assigns Taimoor
the store, RDF population, SPARQL, graph DAL and reproducibility work; Mason owns
ontology/FIBO/native validation, and Shahmeer owns the UI adaptation.

## Current result

- Embedded Oxigraph through pinned `pyoxigraph==0.5.3`; persistent local store,
  RDF/XML import/export and SPARQL SELECT/UPDATE. No server or Docker required.
- All 12 accepted entity types migrated to **356 ABox triples** from the fully
  synthetic M4 seed. All identities, categories, observations and sources remain fictional.
- Six standalone SPARQL files reproduce all six SQL result multisets: row counts
  **8, 2, 5, 5, 5, 17**. Q5 remains a diagnostic candidate listing, not a portfolio total.
- Graph-backed search/details/portfolio/create/update/batch/delete plus seven
  form lookup functions, preserving the M4 dictionary keys and error classes.
- Candidate validation followed by one atomic SPARQL delta; rejected writes
  leave the live graph unchanged. Both the M4 parity bridge and Mason's native
  graph validator run, including capture-file checks at application startup.
- Default startup loads Mason's v1.1.0 ontology into its separate named graph;
  it validates existing data before replacing the ontology. No reasoner is enabled.
- **160 tests passed**: 74 accepted M4, 26 backend, 51 ontology/validation and nine
  runtime integration tests. See [integration verification](docs/backend_integration.md).

The backend and Mason's ontology/native validator are integrated. **Update, 25
November:** Shahmeer's graph-connected UI, its tests, eleven screenshots and the M5
architecture figure are added; see [his contribution](contributions/shahmeer/README.md).
The suite is now **189 passing tests**. The final [three-page report](report/main.pdf)
and [submission ZIP](submission/5_Semantic_Taimoor_Mason_Shahmeer.zip) are available.
The [final revision verification](docs/final_revision_verification.md) records the
compiled-PDF, source-package and diagram checks. Mason's ontology and FIBO/Protégé work are
documented in [his handoff](README_ONTOLOGY.md). No OWL inference is enabled.

## Setup and reproduction

Requirements: Python 3.10+ with SQLite 3.37+ for M4 validation/comparison and a
platform with a pyoxigraph wheel. Tested on Linux, Python 3.12.14; Windows/macOS
installation and UI operation have not been tested in this run.

Run from the repository root:

```sh
python -m venv .venv
# Windows PowerShell: .venv\Scripts\Activate.ps1
# Linux/macOS: source .venv/bin/activate
python -m pip install -r requirements-semantic.txt
python quickstart_semantic.py --compare
python scripts/demo_semantic_crud.py
python quickstart_semantic.py --serve   # graph-backed UI at http://127.0.0.1:5000/
python -m unittest discover -s tests -v
```

The quickstart uses the same accepted, parameterized synthetic seed loader in an
ephemeral SQLite connection to create a reproducible source for migration and SQL
comparison. It never reads or overwrites `data/etf_allocations.sqlite3`.
The application graph DAL reads and writes RDF using SPARQL. The separate SQL
validation/comparison bridge does not answer graph-backed application queries.

The default persistent store directory is `data/semantic_store/` (gitignored).
An existing graph is validated and reused, not reset. For a fresh experiment:

```sh
python quickstart_semantic.py --store data/semantic_trial_01 --compare --export data/trial_01.rdf
```

`--compare` asserts equality with the fresh M4 seed. It is expected to fail if an
existing graph has subsequently been edited. Preserve that graph and choose a
new store path for baseline comparison. Never delete user work to make parity pass.
Custom store directories are not automatically gitignored; do not commit RocksDB files.

The default RDF/XML export is [data/demo.rdf](data/demo.rdf). Its 356 triples
describe instances, not the ontology. The committed ontology is loaded by default.
To explicitly select an alternative RDF/XML ontology:

```sh
python quickstart_semantic.py --ontology path/to/alternative-ontology.owl --compare
```

The ontology graph is atomically replaced by the supplied file, separately from
the data graph. This command stores axioms; it does not activate an OWL reasoner.
The default ontology's terms match the committed backend vocabulary. A custom
ontology is not automatically checked for vocabulary alignment. Regenerate
data/queries together if the contract changes.

## Runtime configuration and operations

The store is embedded: its path replaces a network endpoint configuration.
Use **one shared GraphDatabase instance in one application process**. Its RLock
serializes application writers; RocksDB prevents a second process opening the
same writable directory. Do not use multiple Flask workers or the debug reloader
with independent writable store instances. There is no public SPARQL endpoint.

```python
from semantic.runtime import open_graph_database
from semantic import repositories, lookups

graph = open_graph_database('data/semantic_store')
rows = repositories.search_disclosures(graph, ticker='SYA', dimension_name='Geography')
details = repositories.get_disclosure_detail(graph, snapshot_id=1)
portfolio = repositories.get_customer_portfolio(
    graph, '1001', portfolio_id=1, holding_as_of_date='2026-08-01')
```

Make `src` importable in the app entry point, as in the accepted M4 application.
Use the graph modules instead of the SQL modules for M5 routes. Shahmeer's integrated Flask routes use these graph modules by default; the accepted
SQLite backend remains selectable for regression.
Use this factory once at application startup and share the returned instance; it
attaches `make_backend_validator(capture_root=ROOT)`, validates existing data and
loads the ontology. Constructing the lower-level `GraphDatabase` without a callback
still runs only the legacy parity bridge; it is not the integrated startup path.
All reads execute SPARQL SELECT; writes execute SPARQL INSERT/DELETE over a
candidate graph, validate, and publish the exact delta in one store update.

## Files and handoff

| Artifact | Purpose |
| --- | --- |
| `src/semantic/vocabulary.py` | Central proposed namespaces, identity and property mapping |
| [Vocabulary proposal](docs/vocabulary_proposal.json) | Machine-readable proposed class/property mapping for Mason |
| [Integration contract](docs/integration_contract.md) | API, validation callback, concurrency and identity details |
| `src/semantic/codec.py`, `store.py` | RDF population, strict migration checking and transactional boundary |
| `src/semantic/runtime.py` | Shared startup with native validation, source-file checks and default ontology |
| `src/semantic/repositories.py`, `lookups.py` | Graph-backed application operations |
| `src/semantic/sparql/01_*.sparql` through `06_*.sparql` | Six analytical SELECT files |
| `quickstart_semantic.py` | Fresh creation/reuse, ontology load, RDF/XML export and comparison |
| `scripts/demo_semantic_crud.py` | Executed create/edit/delete and rollback examples on a temporary graph |
| `tests/test_semantic_backend.py` | 26 semantic behavioral/parity checks |
| `tests/test_semantic_runtime.py` | Nine tests of actual startup, callback invocation and native rollback |
| [Verification evidence](docs/verification.json) | Observed setup, parity and test results |
| [Backend report section](report/taimoor_semantic_section.tex) | Integrated graph population, operations and executable SELECT/results |

## Requirements and final deliverables

Manual 5.1: Mason supplied the ontology, meaningful restrictions, FIBO mapping,
Protégé evaluation and documented OWL-versus-validation limits. Manual 5.2
allows an alternative RDF/XML/SPARQL-capable store with documented installation.
Manual 5.3: population, six SELECT examples and graph DML are implemented here.
Manual 5.4: done. The UI runs on the graph and its route tests rerun on the graph.
Architecture figure: [figures/system_architecture_m5.pdf](figures/system_architecture_m5.pdf);
screenshots: [docs/screenshots](docs/screenshots/), reproducible with
`python scripts/capture_ui_screenshots.py` (needs `pip install playwright` and
`python -m playwright install chromium`).
The team report must be **exactly three ACM sigconf pages**, including references,
and the final ZIP must be `5_Semantic_Taimoor_Mason_Shahmeer.zip` with sources and PDF.
The repository link belongs in the report title footnote and abstract.

The current repository has no project-wide LICENSE. The [repository access and reuse policy](../../README.md#license-and-access)
permits course evaluation and asks other users to contact the authors about reuse.
Third-party dependencies retain their own licenses.

## AI assistance and evidence

AI assisted with implementation, SPARQL translation, tests, documentation and the
report fragment, and actually ran the recorded checks. Mason subsequently aligned
his ontology and validator to the backend. These are not claims that
Taimoor personally executed tests or that
the professor approved implementation choices. The manual requires students to
critically evaluate AI-generated work and disclose/cite assistance.

Technical references: [Oxigraph Store](https://pyoxigraph.readthedocs.io/en/stable/store.html),
[RDF parsing/serialization](https://pyoxigraph.readthedocs.io/en/stable/io.html),
[SPARQL 1.1 Query](https://www.w3.org/TR/sparql11-query/), and
[SPARQL 1.1 Update](https://www.w3.org/TR/sparql11-update/).
