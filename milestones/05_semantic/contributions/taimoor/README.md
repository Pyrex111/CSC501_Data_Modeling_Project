# Taimoor: Milestone 5 backend and report evidence

Responsibilities: RDF population, Oxigraph setup, SPARQL queries, graph data access,
validation integration and reproducibility. The implementation and automated
verification were AI-assisted; human evaluation is a separate course requirement.

## Implementation already delivered

- `f03f150`: initial persistent graph backend, 356 synthetic ABox triples, six
  SQL-equivalent SPARQL analyses, graph repositories/lookups, staged writes,
  quickstart and 26 semantic tests.
- `4f09d50`: shared `semantic.runtime.open_graph_database`, default ontology load,
  Mason's native validation callback with capture-file checks, retained M4 parity
  checks, and nine runtime integration tests. The suite then passed 160 tests.
- Shahmeer's subsequent UI integration reused that startup and brought the suite
  to 189 tests. His application work and Mason's ontology work remain theirs.

## Remaining report contribution delivered here

- [Report section](../../report/taimoor_semantic_section.tex): concise backend
  explanation, actual SELECT, observed result table, semantics and validation.
- [Executable report example](../../report/examples/taimoor_snapshot_totals.sparql):
  a compact projection of Q3, compared against the independent SQL result.
- [Query evidence](../../docs/taimoor_query_evidence.json): exact output, source
  hash and all six complete-result comparisons.
- [Backend and package review](../../docs/taimoor_final_review.md): checked claims,
  remaining report corrections, and explicit final-package approval boundary.

Mason must include the `report/examples/` directory when rebuilding the submission
source ZIP: the revised section reads the displayed query from that file. This
contribution does not merge PR #2 or replace the existing compiled PDF/ZIP before
the remaining team corrections and page/layout checks.
