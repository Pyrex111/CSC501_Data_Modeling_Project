# Milestone 5 submission criteria audit

Basis: the supplied `5_Semantic_Manual(2).pdf`, especially pages 1, 3, 6 and
11–14. Reviewed the final report/package published at `ede296f` and the linked
implementation. Checks were executed by ChatGPT/Codex; human evaluation is not
inferred from automated success. Subsequent README corrections do not change the
report PDF, ZIP, application, ontology or query files.

| Criterion | Evidence and result |
| --- | --- |
| Format, author list, repository and naming (10%) | Exactly three English ACM `sigconf` pages using acmart v2.20 (2026-08-16); all three authors included. All members are graduate students per the team's supplied information, so the retained last author is also a graduate student. Repository URL appears in the title footnote and abstract. ZIP is named `5_Semantic_Taimoor_Mason_Shahmeer.zip`. |
| Report: conversion, triples, DML, especially SELECT (40%) | Explains all twelve relations, association classes, properties, identifiers, FIBO reuse, OWL/validation split, 356 instance triples, staged INSERT/DELETE operations and six analytical SELECTs. Table 3 displays an executable SELECT and its actual five-row result. Six full SQL/SPARQL result multisets match; row counts are 8, 2, 5, 5, 5, 17. |
| Code architecture (20%) | UI, business helpers, graph repositories/lookups, driver/store, ontology and data are separated. Figure 1 correctly shows routes calling helpers and graph access separately. `open_graph_database()` attaches both validation layers and loads the ontology; UI shares its instance. |
| README (10%) | Project overview, requirements, installation, semantic commands, store/configuration, query/CRUD reproduction, access/reuse policy and third-party notices are available. Stale pending-report text and broken report links were corrected. There is no project-wide open-source grant; the documented policy permits course evaluation and requires author contact for other reuse. |
| Quickstart (10%) | Fresh `quickstart_semantic.py --compare` creates the store, loads 504 ontology triples and 356 instance triples, exports RDF/XML and passes all six comparisons. `--serve` builds and starts the graph-backed Flask application with one graph instance. |
| Repeatable demonstration (10%) | Fresh temporary-store run and CRUD demonstration succeeded. Invalid Complete edits/deletions and final-entry deletion preserved the graph. HTTP search, filtered search, detail, create and portfolio pages returned 200 with the graph banner. Existing full suite passed 189 tests in the immediately preceding final revision. Eleven original readable, numbered screenshots are included byte-for-byte. |
| Ontology and model integrity (manual 5.1, 5.5) | RDF/XML parses; 12 project classes, 17 object properties and 37 datatype properties, with declared domains/ranges. Instance classes and project predicates are declared in the ontology. CLI validation reports 356 triples, zero issues. Explicit validation handles sums, duplicate rejection and file existence; no OWL reasoner is claimed. Protégé inspection records are documented separately. |
| Permitted triple store (manual 5.2) | The manual expressly permits another RDF/XML/SPARQL store with setup instructions. Embedded Oxigraph is documented and exercised; Virtuoso is not mandatory. |
| User interface (manual 5.4) | Entry, search/filter/retrieval, batch updates and deletion use the graph repositories. Rejection feedback and graph-preservation behavior are covered by tests/screenshots. |
| Submission files | ZIP contains matching compiled PDF and all required LaTeX/BibTeX/class/style/table/query/figure sources, plus eleven screenshots. All 29 manifest checksums and ZIP integrity pass. Extracted sources compiled to identical three-page text and rendered pixels. Implementation files may be supplied through the accessible linked repository. |
| Individual contributions (manual 5.5.2) | Git history contains the accounts Pyrex111, Mason0217 and shahmeerather, plus contribution records and substantive backend, ontology and UI work. |
| AI disclosure (manual page 1, category D) | Report Section 4.1 and bibliography cite both ChatGPT/Codex and Claude; contribution notes describe their roles. No mandatory category-C editing appendix is specified for this category-D task. |
| Human critical evaluation (manual page 1, category D) | **Requires actual author review.** Automated tests cannot establish that a student critically evaluated the output. The report discusses the modelling tradeoffs and existing notes distinguish human review from AI-executed evidence; the submitting author must personally review the final prose and these decisions before submission. |

Final ZIP SHA-256:
`eebde45297da45235cf458666d842ef86ec2c29e0b4cd6ca5ea0fdfc5125dd94`.

Final PDF SHA-256:
`fe1a03b1fae5d2a0da116f7c306f06f1007474129173be49c6d2fad6156fb5cb`.

This is evidence of the checked requirements, not a prediction of the marker's
score. Review the distinction between a dated disclosure and an intended
allocation, OWL identity inference and duplicate rejection, and the provisional
0.005 tolerance on synthetic Complete snapshots. Student agreement with those
choices must be real and must not be fabricated as an executed experiment.
