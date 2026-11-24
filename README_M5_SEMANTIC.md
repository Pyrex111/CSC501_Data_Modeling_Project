# M5 Semantic Layer — package guide

This zip contains Mason's Milestone 5 work, laid out in the repository hierarchy and
aligned with the accepted graph backend (`milestone5/taimoor-semantic-backend`,
`f03f150`). The report section is **not** in this package on purpose: the three-page
paper has to wait for Taimoor's SPARQL statements and Shahmeer's application
section.

**How to upload.** Extract, then add the items below to the repository root with
*Add file → Upload files*, **on a new branch** (`milestone5/mason-ontology`) rather
than on `main`, because the backend branch is still unmerged:

```
src/                 ontology, validator, backend hook        (new files inside an existing tree)
tests/               test_semantic_ontology.py                 (new file)
milestones/          05_semantic: README_ONTOLOGY, docs, figures (new files inside an existing tree)
requirements.txt     one added line: rdflib>=7.0               (replace — re-apply the line
                                                                if it changed meanwhile)
```

Do **not** replace `milestones/05_semantic/README.md`: the backend owner maintains
that file with the setup and reproduction instructions. This package ships
`README_ONTOLOGY.md` beside it instead.

`README_M5_SEMANTIC.md` (this file) is a package guide. It is not the repository's
own `README.md`, so uploading it adds a file rather than overwriting the team's
front page; skip it if you would rather keep the root clean.

**Read this first:** `milestones/05_semantic/README_ONTOLOGY.md`. It states what was
built, the interface rules the other two owners need, the Protégé inspection
readings, and the known limits. Then read
`milestones/05_semantic/docs/backend_alignment.md` for the six vocabulary decisions
and the verification log.

**What is where**

| Path | What it is |
| --- | --- |
| `src/dal/models/semantic/etf_allocations.owl` | the ontology, TBox only, 12 classes, version 1.1.0 |
| `src/dal/models/semantic/graph_validation.py` | explicit graph checks plus a CLI |
| `src/dal/models/semantic/backend_bridge.py` | adapter for `GraphDatabase(validator=...)` |
| `tests/test_semantic_ontology.py` | 51 tests; branch suite becomes 151 |
| `milestones/05_semantic/README_ONTOLOGY.md` | the technical readme, start here |
| `milestones/05_semantic/docs/` | namespace/identity, mapping, FIBO alignment, backend alignment |
| `milestones/05_semantic/docs/figures/` | Protégé inspection screenshots (1.0 labels) |

**Quick check after uploading** (from the repository root):

```bash
pip install -r requirements.txt
python -m unittest discover -s tests                    # expect 151 tests OK
python -m dal.models.semantic.graph_validation milestones/05_semantic/data/demo.rdf
                                                        # expect 356 triples, 0 issues
python -m dal.models.semantic.graph_validation --rules
```

Verified before packaging by overlaying exactly these items onto a copy of the
backend branch: the full suite reported **151 tests OK**, the validator reported
**0 issues on the 356-triple ABox**, every ABox class and predicate was declared in
the TBox, and the quickstart loaded the ontology and still matched all six SQL
results. Nothing in Milestone 4 was touched.
