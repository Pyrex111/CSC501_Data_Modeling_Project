# Mason: Milestone 5 ontology, graph validation and report assembly

Prepared 25 November 2026, on top of `main` after the backend and UI contributions
merged. Responsibility: the OWL ontology aligned to the accepted backend
vocabulary, the identity/provenance policy, the explicit graph validator and its
backend hook, the model tests, the contribution documentation, and the assembled
three-page team report. This is an AI-assisted contribution owned by Mason Li.

## What changed

| File | Change |
| --- | --- |
| [src/dal/models/semantic/etf_allocations.owl](../../../../src/dal/models/semantic/etf_allocations.owl) | TBox ontology v1.1.0: 12 classes mirroring the accepted relations; 17 object properties (12 forward + 5 inverse); 37 datatype properties; 4 `hasKey`, 3 disjoint declarations, 1 property chain; seven classes aligned to FIBO / OMG Commons. TBox only, no `owl:imports`, no individuals. |
| [src/dal/models/semantic/graph_validation.py](../../../../src/dal/models/semantic/graph_validation.py) | Explicit checks OWL cannot state: record identity and keys, class/range membership, weight and date consistency, provenance presence; CLI with a `--rules` listing of every enforced rule. |
| [src/dal/models/semantic/backend_bridge.py](../../../../src/dal/models/semantic/backend_bridge.py) | Adapter that binds the native validator into `GraphDatabase(validator=...)`, beside the relational parity checker. |
| [scripts/validate_graph.py](../../../../scripts/validate_graph.py) | CLI wrapper that puts `src` on the import path itself; no `PYTHONPATH` setup required. |
| [tests/test_semantic_ontology.py](../../../../tests/test_semantic_ontology.py) | 51 ontology/model tests: axiom and property counts, domains/ranges, inverses, keys, disjointness, and validator accept/reject cases against synthetic counter-examples. |
| [README_ONTOLOGY.md](../../README_ONTOLOGY.md) | Technical readme: scope, resource-identity rules, Protégé inspection readings and known limits. |
| [docs/](../../docs/) | `namespace_and_identity.md`, `ontology_mapping.md`, `fibo_alignment.md`, `backend_alignment.md`, plus the Protégé inspection screenshots under `docs/figures/`. |
| [report/mason_ontology_section.tex](../../report/mason_ontology_section.tex) | Ontology section for the team report; `report/main.tex` assembles the ontology, backend and UI sections into the three-page paper. |

## How to run

From the repository root:

```sh
python -m pip install -r requirements-semantic.txt
python scripts/validate_graph.py milestones/05_semantic/data/demo.rdf
                                                        # expect 356 triples, 0 issues
python scripts/validate_graph.py --rules
python -m unittest discover -s tests
```

On Windows where the `python` alias opens the Microsoft Store stub, use `py -3` in
place of `python`.

## Evidence

- The 51 ontology tests are part of the full suite, which passes **189 tests OK**.
- The real ABox (`milestones/05_semantic/data/demo.rdf`) holds **356 triples**; the
  validator reports **0 issues**. Every ABox class and predicate is declared in
  the TBox.
- The six SPARQL analyses reproduce the accepted SQL results (8, 2, 5, 5, 5, 17
  rows); that parity check is owned by the backend contribution.
- The compiled team report is [report/main.pdf](../../report/main.pdf): exactly three
  ACM `sigconf` double-column pages.

## Findings while integrating

- The backend vocabulary was still a proposal when the first ontology draft landed;
  the namespaces, property names and datatypes were realigned to the accepted
  `vocabulary.py` and loader output. The six decisions are recorded in
  [docs/backend_alignment.md](../../docs/backend_alignment.md).
- Rules OWL can state (domains, ranges, inverses, keys, disjointness) stay in the
  ontology; rules that need record-level arithmetic or cross-record checks stay in
  the explicit validator. That split is documented in the report's rule-split table.
- FIBO is referenced, not imported: seven classes reuse FIBO / Commons parent
  terms, and no FIBO file ships with the project.

## AI use

OpenAI ChatGPT/Codex assisted with ontology drafting, validator code, tests,
documentation and report prose; Mason reviewed and edited each contribution. All
demonstration records are synthetic; no real customer, fund or source document is
used.
