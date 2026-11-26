# Alignment with the Accepted Graph Backend

Milestone 5. Owner: Mason Li (ontology and semantic validation).

Reference: branch `milestone5/taimoor-semantic-backend`, commit `f03f150`
(20 November 2026, 24 files), and its
`docs/vocabulary_proposal.json` plus `docs/integration_contract.md`. The backend's
own README states that the vocabulary is "a proposal for Mason's agreement" and
that the temporary SQL-parity bridge must stay until Mason supplies native graph
rules. This note records what was agreed, what was changed, and what the change was
verified against.

## 1. The six decisions

| # | Decision | Consequence |
| --- | --- | --- |
| D1 | One namespace: `.../CSC501_Data_Modeling_Project/ontology#`, TBox IRI `.../ontology`, data `.../resource/{Table}/{Id}` | TBox axioms now apply to the 356 ABox triples that already exist; no data regeneration |
| D2 | Object property names follow `vocabulary.py` | 8 local names renamed; 5 inverse pairs kept; 17 object properties total |
| D3 | Datatype property names follow the accepted column names, not invented semantic labels | 6 columns renamed; `label`, `code`, `version`, `url`, `baseCurrency`, `weightFraction` |
| D4 | Datatypes follow what the loader writes: `REAL` → `xsd:double`, URLs → `xsd:string` | weight ranges and URL ranges re-declared; `xsd:decimal` withdrawn |
| D5 | Resource IRIs are record handles, with `recordId` declared in the TBox | business identity stays in `owl:hasKey` plus explicit checks; ID-reuse hazard documented |
| D6 | The validator is exposed as a backend hook with the contract's signature | `GraphDatabase(path, validator=...)` can use the same rule set the tests prove |

## 2. Object properties: what changed

| First draft (1.0) | Accepted ABox (1.1.0) | Direction |
| --- | --- | --- |
| `hasIssuer` | `offeredBy` | ETF → ETFProvider |
| `holdingOfPortfolio` | `inPortfolio` | Holding → Portfolio |
| `holdingAsset` | `holdsETF` | Holding → ETF |
| `snapshotOfETF` | `describesETF` | Snapshot → ETF |
| `fromSource` | `supportedBy` | Snapshot → SourceDocument |
| `entrySnapshot` | `inSnapshot` | Entry → Snapshot |
| `entryCategory` | `usesCategory` | Entry → Category |
| `usesScheme` | `definedBy` | Category → Scheme |

Unchanged because they already matched: `ownedBy`, `identifiesETF`, `publishedBy`,
`hasDimension`. Kept from the first draft as inverses for traversal and for rules
written in the collection direction: `owns`, `hasHolding`, `hasSnapshot`,
`hasIdentifier`, `hasEntry`. Twelve foreign-key names plus five inverses is 17.

The ABox stores only the foreign-key direction. Because rdflib performs no
reasoning, `graph_validation` closes each inverse pair in memory before checking
and the bridge does the same for a candidate store — otherwise an at-least-one rule
stated on `hasEntry` would fire on an ABox that stores `inSnapshot`.

## 3. Datatype properties: what changed

| First draft (1.0) | Accepted ABox (1.1.0) | Reason |
| --- | --- | --- |
| `portfolioCurrency`, `fundCurrency` | `baseCurrency` (one property, union domain) | the column is `BaseCurrency` in both relations and the ABox writes one predicate |
| `declaredWeight`, `holdingWeight` | `weightFraction` (one property, union domain) | the column is `WeightFraction` in both relations |
| `sourceUrl` | `url` | the column is `Url` |
| `categoryLabel` | `label` | the column is `Label` |
| `categoryCode` | `code` | the column is `Code` |
| `schemeVersion` | `version` | the column is `Version` |
| — | `recordId` (new) | the loader exports every row's integer `Id`; without a declaration the ABox would use an undeclared predicate |

Totals: 38 scalar columns collapse to 36 distinct predicates, plus `recordId`,
which gives 37 datatype properties. The test suite pins 12 classes, 17 object
properties and 37 datatype properties.

## 4. Identity, and the cost of record handles

The accepted rule is `res:{Table}/{Id}`, with `recordId` on every individual. The
TBox declares `recordId` with a union domain and an integer range, and deliberately
does **not** declare `owl:hasKey(recordId)`: that would make the local row handle a
global identity axiom and freeze an artefact of SQLite into the ontology.

Business identity remains where the relational model puts it — four `owl:hasKey`
declarations and eight explicit composite checks. The full table is in
`docs/namespace_and_identity.md`, section 3.

The cost is that `MAX(Id)+1` allocation recycles an IRI when the highest row is
deleted. Mitigations adopted: aggregates are append-only; retired identifiers are
not recycled; the IRIs are not published as permanent external identities. If the
vocabulary is ever exposed externally, a separate identity layer is required, and
that layer is not invented here.

One consequence specific to this dataset: `ETF` has no unique key of its own, so an
ETF's identity currently rests on its row plus its identifier set. The explicit
"at least one identifier" rule guarantees the set is non-empty; it does not
guarantee that the row is the only fund with that name. This is recorded as a
known limit rather than papered over.

## 5. The validation hook

The contract asks for a callable that receives the candidate `Store`, inspects it
read-only, returns `None` on success, and raises
`dal.schema_validation.ModelIntegrityError` on failure. `backend_bridge.py`
implements exactly that:

```python
from semantic.store import GraphDatabase
from dal.models.semantic.backend_bridge import validate_candidate_store

graph = GraphDatabase('data/semantic_store',
                      validator=validate_candidate_store,
                      capture_root='.')
```

`graph_from_store` reads **only** `.../graph/data`, maps pyoxigraph terms to rdflib
terms, and hands the graph to `collect_issues`. The ontology graph is ignored on
purpose: TBox axioms are not ABox assertions, and the backend enables no reasoner.
`make_backend_validator(capture_root=...)` binds the capture root once when the
application wants the file-existence rule active.

The backend runs its temporary SQL-parity bridge first and this hook second, so
nothing is removed by adopting it. The bridge can be retired once the graph rules
have run against an edited candidate in the integrated application; that is a
decision for the backend owner, and the evidence below is what it should be based
on.

## 6. Verification actually run

| Check | Command | Result |
| --- | --- | --- |
| Combined test suite | `python -m unittest discover -s tests` | **151 tests OK** (74 accepted M4 + 26 backend semantic + 51 Mason) |
| Validator against the real ABox | `python scripts/validate_graph.py milestones/05_semantic/data/demo.rdf` | 356 triples, **0 issues** |
| Term coverage | test compares ABox predicates and classes with the TBox | **0 undeclared predicates, 0 undeclared classes** |
| Ontology loads into the store | `python quickstart_semantic.py --store ... --compare --ontology src/dal/models/semantic/etf_allocations.owl` | ontology accepted; **6/6 SPARQL results match SQL** (`full_result_match: true`) |
| Hook on a candidate store | test loads the ABox into `pyoxigraph.Store`, validates, then injects a second weight | returns `None`, then raises `ModelIntegrityError` |
| Protégé re-inspection | Protégé 5.6.9, RDF/XML, read-only | axiom 332, **Class 19 / Object 19 / Data 39 / Individual 0**, SubClassOf 33, Disjoint 3, imports 0 |

The 51 Mason tests comprise 47 rule and structure tests from the first draft plus
four alignment tests; three of the four skip when the backend modules or its ABox
export are absent, and all four run on this branch.

## 7. Remaining disagreements and risks

1. **Shared `weightFraction`.** One predicate carries two meanings. The class
   disambiguates, but a query that does not filter by class can mix holdings and
   entries. Splitting the column in the backend would let the ontology restore
   `fibo:hasFractionalInterest` for holdings.
2. **ID reuse.** See section 4. Append-only discipline is the current mitigation.
3. **No reasoner.** Loading the TBox stores axioms; it does not classify. Every
   rule needing closure, counting or distinctness is restated in code, and the
   split is printed by `--rules`.
4. **Protégé screenshots predate the rename.** The two files in `docs/figures/`
   were captured on version 1.0 and show the old local names. The class tree and
   the six `AllocationSnapshot` axioms are unchanged in shape; the 1.1.0
   re-inspection read **39 data properties**, not 41, and the full readings are in
   the README's inspection record.
