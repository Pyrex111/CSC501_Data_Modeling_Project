# Milestone 5 — Semantic Web Layer

Ontology, identity policy, FIBO alignment, explicit graph validation, backend hook,
and model tests for the accepted Milestone 4 model. Owner: **Mason Li**. AI
assistance is disclosed in report Section 4.1 and the contribution notes, as course
policy requires (category D).

This package is the part of the milestone that does not depend on the other two
work-streams, and it is now aligned with the accepted graph backend
(`milestone5/taimoor-semantic-backend`, `f03f150`). Milestone 4 is untouched and
still runs; nothing here changes the twelve-table schema or the Flask application.

**Final integration:** the complete three-page [report](report/main.pdf) and
[submission ZIP](submission/5_Semantic_Taimoor_Mason_Shahmeer.zip) are now available.
The historical ontology-only handoff below describes its original scope; current
setup instructions and the 189-test suite are in [README.md](README.md).

**This file is `README_ONTOLOGY.md`, not `README.md`.** The backend owner already
maintains `milestones/05_semantic/README.md`; overwriting it would delete his setup
instructions. Apply this package as an overlay instead of replacing that file.

## What this package contains

| Path | What it is |
| --- | --- |
| `src/dal/models/semantic/etf_allocations.owl` | the ontology (TBox only, RDF/XML, no individuals), version 1.1.0 |
| `src/dal/models/semantic/graph_validation.py` | explicit checks over an RDF graph, plus a CLI |
| `src/dal/models/semantic/backend_bridge.py` | adapter that plugs those checks into `GraphDatabase(validator=...)` |
| `src/dal/models/__init__.py`, `src/dal/models/semantic/__init__.py` | package markers |
| `tests/test_semantic_ontology.py` | 51 tests: ontology shape, rule behaviour, backend alignment |
| `milestones/05_semantic/docs/namespace_and_identity.md` | namespaces, datatypes, record-handle identity, context keys, provenance |
| `milestones/05_semantic/docs/ontology_mapping.md` | relation-by-relation mapping and the OWL-versus-explicit split |
| `milestones/05_semantic/docs/fibo_alignment.md` | what is reused, extended, and refused |
| `milestones/05_semantic/docs/backend_alignment.md` | the six vocabulary decisions, the rename tables and the verification log |
| `milestones/05_semantic/docs/figures/` | Protégé inspection evidence, two crops without local paths (1.0 labels) |
| `requirements.txt` | one added line: `rdflib>=7.0` |

Upload as an overlay onto the Milestone 5 branch: `src/`, `tests/`,
`milestones/`, and `requirements.txt`. `requirements.txt` is a replace-style upload;
re-apply the `rdflib` line if it changed in the meantime. Do not overwrite
`milestones/05_semantic/README.md`.

## What was completed

1. **Mapping the accepted model onto an ontology.** Twelve relations become twelve
   classes, not a sample. The schema has 51 non-`Id` columns: 13 foreign keys become
   17 object properties (12 distinct names, because `hasDimension` serves two
   columns, plus five declared inverses), and 38 scalar columns become 36 distinct
   predicates plus `recordId`, which is 37 datatype properties. `Holding` and
   `AllocationEntry` stay association classes, because the weight (and the holding's
   date) belongs to the relationship rather than to an endpoint.
2. **Classes, properties, domains, ranges, restrictions.** 26 restrictions across
   nine classes, eleven functional object properties plus a functional `recordId`,
   four `owl:hasKey` declarations, three disjointness axioms, one property chain, and
   union domains for `hasDimension`, `baseCurrency`, `weightFraction` and
   `recordId`. Every property carries an explicit domain and range, and a test
   enforces that.
3. **FIBO alignment.** Seven classes specialise published FIBO terms. Three FIBO
   properties are reused as super-properties (the weight and both as-of dates) plus
   two Commons collection properties. Two candidates are **refused and documented**:
   the investment-policy classes, because FIBO records an intended allocation while
   this model records a dated disclosure, and the `Publisher` role, because one
   relation here plays both issuer and publisher. A third is refused as redundant
   (`BasketConstituent`, already covered by `WeightedBasketConstituent`).
4. **Namespace and identity rules.** Terms live in `.../ontology#`, individuals in
   `.../resource/{Table}/{Id}`. Identifiers are record handles, not business keys:
   business identity is carried by four `owl:hasKey` declarations and eight explicit
   uniqueness checks. The category context key is built exactly as the relational
   validator builds it, and a test asserts that the two helpers return
   byte-identical strings. The identifier-reuse hazard is documented instead of
   denied.
5. **Graph validation, with the split documented.** Weight ranges, `Complete` totals
   within 0.005, dimension agreement, required identifiers and non-empty
   disclosures, plus closed value sets, ISIN/ticker shapes, date lexical forms,
   NOT NULL slots, single-valued clashes, composite uniqueness, and capture-file
   existence. `OWL_ENFORCED_RULES` and `EXPLICIT_RULES` record which rule lives where,
   and `--rules` prints them without needing a data file.
6. **Model tests and backend integration.** 51 tests in this package; on the branch
   the repository suite is 151 (74 accepted M4 + 26 backend + 51 here), all passing.
   The validator reports **0 issues on the backend's synthetic 356-triple ABox**, and the
   ABox uses **no undeclared class or predicate**.

## Verify it yourself

```bash
python -m pip install -r requirements-semantic.txt
python -m unittest discover -s tests   # 189 in the integrated application
python scripts/validate_graph.py milestones/05_semantic/data/demo.rdf
python scripts/validate_graph.py --rules
python quickstart_semantic.py --compare \
    --ontology src/dal/models/semantic/etf_allocations.owl --store /tmp/m5check
```

`--rules` prints the OWL/explicit split and needs no file. Passing the ABox path
gives the same rule set the application hook applies. The quickstart loads the TBox
into the `graph/ontology` named graph and still reproduces all six SQL results
(`full_result_match: true`).

## The hook, for the backend and the UI

```python
from semantic.store import GraphDatabase
from dal.models.semantic.backend_bridge import validate_candidate_store

graph = GraphDatabase('data/semantic_store', validator=validate_candidate_store)
```

The hook reads only the data graph, never mutates the candidate, returns `None` on
success and raises `ModelIntegrityError` with one message per violation. It closes
the five `owl:inverseOf` pairs before checking, because the ABox stores only the
foreign-key direction. Bind `capture_root` with
`make_backend_validator(capture_root=...)` when the file-existence rule should run.

## Protégé inspection record

Two read-only inspections, both in Protégé 5.6.9 on Windows, opening the file as
RDF/XML.

| Reading | Version 1.0 (2026-11-22) | Version 1.1.0 (2026-11-23) |
| --- | --- | --- |
| Axiom count | 333 | **332** |
| Logical axiom count | 173 | **171** |
| Declaration axiom count | 67 | **66** |
| Class entities | 19 (12 relation classes + 7 FIBO superclasses) | **19** |
| Object properties | 19 (17 declared + 2 Commons) | **19** |
| Data properties | 41 (38 declared + 3 FIBO) | **39** (37 declared + 2 FIBO: `hasWeight`, `hasAsOfDate`) |
| Individuals | 0 | **0** |
| SubClassOf | 33 (7 reuse + 26 restrictions) | **33** |
| DisjointClasses | 3 | **3** |
| Direct imports | 0 | **0** |

The data-property count fell from 41 to 39 because the two weight properties
merged into one declared property and the two FIBO weight super-properties
(`hasWeight`, `hasFractionalInterest`) collapsed with them; the two as-of dates
keep one shared FIBO super-property. The class tree, the object properties and the
26 restrictions are unchanged in shape.

The two screenshots in `docs/figures/` were captured on version 1.0 and carry the
old local names (`snapshotOfETF`, `fromSource`); they are kept as inspection
evidence, and the labels are the only difference.

`docs/figures/protege_class_hierarchy.png` shows the tree with the seven FIBO
parents nested above their subclasses, which is why the tree reads twelve top-level
entries instead of twelve flat rows.
`docs/figures/protege_snapshot_description.png` shows `AllocationSnapshot`'s six
restrictions, its `WeightedBasket` parent and two disjointness axioms. The ontology
was inspected read-only and not re-saved in either run.

## What the next two owners need from here

**Instance data (Taimoor).** The vocabulary now matches `src/semantic/vocabulary.py`;
no regeneration is required. If a column is ever renamed, change the central map and
regenerate the ABox and the six SPARQL files together. Values are `xsd:date`, UTC
`xsd:dateTime` (`Z` or `+00:00`), `xsd:double` for weights, `xsd:string` elsewhere.
`recordId` is declared, so the ABox no longer contains an undeclared predicate. Keep
`MAX(Id)+1` allocation append-only, as section 3 of the identity note explains.

**Application (Shahmeer).** A snapshot's weights are reachable through `hasEntry` /
`usesCategory` / `weightFraction` (or the stored direction `inSnapshot` /
`usesCategory`). `coverageStatus` tells the UI whether a total is expected to sum to
one; `supportedBy` and `sourceLocator` cite a number back to its capture. Displayed
totals should come from SPARQL rather than be summed in the application, so the
tolerance rule stays in one place. Filter `weightFraction` by class: holdings and
entries share the predicate.

**Agreed terminology.** `AllocationSnapshot` is one dated disclosure block,
`AllocationEntry` one weight inside it, `AllocationCategory` a label scoped to one
dimension and one context key. They are deliberately not called "allocation",
"holding" or "sector", because a snapshot is an observation, not a target.

## Position to defend in the report

1. The ontology covers all twelve relations, not a sample: 51 non-`Id` columns
   become 17 object properties and 37 datatype properties, with the arithmetic
   pinned by tests.
2. `Holding` and `AllocationEntry` stay association classes, because the weight (and
   the holding's date) belongs to the relationship.
3. FIBO is reused by reference at seven classes and three properties, plus two
   Commons collection properties, and refused twice — the investment-policy classes
   (observation is not intent) and the publisher role (one relation plays two
   roles). The refusals are argued, not glossed.
4. OWL states shape and can express closed literal ranges and parent-scoped keys.
   This implementation keeps value lists and parent-scoped duplicate rejection in
   explicit validation; OWL keys infer identity rather than reject duplicate rows.
   Aggregated totals and filesystem facts also need explicit checks. The four
   dimension triggers become a property chain *and* an explicit check.
5. The graph and the database agree byte-for-byte on context keys, and a test
   enforces that agreement rather than asserting it in prose.
6. The same rule set runs on the CLI, on a candidate store through the hook, and
   against the backend's real ABox — the alignment is measured, not claimed.

## Known limits, stated plainly

- No `owl:AllDifferent` on dimension individuals, so a dimension mismatch is
  invisible to a reasoner alone; the explicit check catches it instead.
- `Sector` and `Geography` are not individuals in the ontology, so the closed value
  set is checked in code rather than in OWL.
- `weightFraction` carries two meanings, distinguished by class. A query that does
  not filter by class can mix holdings and entries.
- `Max(Id)+1` allocation can recycle an IRI after deleting the highest row; these
  IRIs are not fit for permanent external publication.
- An ETF has no unique key of its own in the accepted schema; identity rests on the
  row plus the identifier set.
- `capturedFileRef` proves a capture exists, never that it supports the numbers.
  Under the synthetic dataset these files are generated.
- FIBO is referenced by IRI and not imported, so the file works offline; a consumer
  with FIBO loaded still sees the subsumptions.
