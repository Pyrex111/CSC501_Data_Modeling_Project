# ER and Relational Schema to Ontology Mapping

Milestone 5, semantic layer. Owner: Mason Li (ontology and semantic validation),
with AI assistance disclosed in the contribution notes.

The accepted Milestone 4 model is unchanged. This document maps it, relation by
relation, onto the ontology in `src/dal/models/semantic/etf_allocations.owl`, and
states for each constraint whether the graph carries it as an OWL axiom or only as
an explicit check.

Names and datatypes follow the accepted graph backend's central vocabulary
(`src/semantic/vocabulary.py`, proposal accepted on 20 November 2026), so the
TBox computes over the ABox that already exists rather than over a parallel
spelling of it. `docs/backend_alignment.md` lists every name that changed when
this alignment was made.

## 1. Correspondence scheme

The scheme is the one the manual prescribes, applied without shortcuts:

| Schema construct | Ontology construct |
| --- | --- |
| entity set (relation) | `owl:Class` |
| row | individual in the `res:` namespace, with `recordId` |
| non-key attribute column | `owl:DatatypeProperty`, named by the column's lower camel case |
| foreign key column | `owl:ObjectProperty` from the central map |
| IS-A between entity sets | `rdfs:subClassOf` (used only for FIBO reuse) |
| 1..1 / exactly-one participation | `owl:qualifiedCardinality 1` restriction |
| at least one | `owl:minQualifiedCardinality 1` |
| at most one | `owl:maxQualifiedCardinality 1` |
| `UNIQUE` on a clean key | `owl:hasKey` |
| `UNIQUE` naming a parent | explicit uniqueness check (no IRI minting) |
| relationship with its own attributes | association class, not a bare property |
| `CHECK (x IN (...))` | explicit check (see Section 4) |

Column counts confirm the mapping is complete rather than sampled: the accepted
schema has 51 non-`Id` columns, of which 13 are foreign keys and 38 are scalar.

- **Object properties: 17.** The 13 foreign keys collapse to 12 distinct names
  (`hasDimension` serves both the snapshot and the category column), and five
  inverses are declared for traversal (`owns`, `hasHolding`, `hasSnapshot`,
  `hasIdentifier`, `hasEntry`). 12 + 5 = 17.
- **Datatype properties: 37.** The 38 scalar columns collapse to 36 distinct
  predicates because `BaseCurrency` appears in two relations and `WeightFraction`
  in two, and one more property, `recordId`, carries the row handle the
  application still uses. 36 + 1 = 37.

The arithmetic is asserted in the test suite, not only here.

## 2. Relation-by-relation

| Relation | Class | Columns to datatype properties | Foreign keys to object properties |
| --- | --- | --- | --- |
| `Customer` | `etf:Customer` | `customerNumber`, `givenName`, `familyName`, `email` | — |
| `ETFProvider` | `etf:ETFProvider` | `legalName`, `registrationNumber`, `registrationJurisdiction`, `websiteUrl` | — |
| `AllocationDimension` | `etf:AllocationDimension` | `dimensionName` | — |
| `ClassificationScheme` | `etf:ClassificationScheme` | `schemeAuthority`, `schemeName`, `version`, `definitionUrl` | — |
| `Portfolio` | `etf:Portfolio` | `portfolioReference`, `portfolioName`, `baseCurrency` | `ownedBy` → Customer (inverse `owns`) |
| `ETF` | `etf:ETF` | `fundName`, `domicileCountryCode`, `baseCurrency`, `inceptionDate` | `offeredBy` → ETFProvider |
| `ETFIdentifier` | `etf:ETFIdentifier` | `identifierScheme`, `identifierValue`, `exchangeContext` | `identifiesETF` → ETF (inverse `hasIdentifier`) |
| `Holding` | `etf:Holding` | `weightFraction`, `holdingAsOfDate` | `inPortfolio`, `holdsETF` (inverse `hasHolding`) |
| `SourceDocument` | `etf:SourceDocument` | `url`, `retrievedAt`, `publishedAt`, `capturedFileRef`, `documentTitle` | `publishedBy` → ETFProvider |
| `AllocationCategory` | `etf:AllocationCategory` | `label`, `code`, `contextKey` | `hasDimension` → Dimension; `definedBy` → Scheme (optional) |
| `AllocationSnapshot` | `etf:AllocationSnapshot` | `allocationAsOfDate`, `basisNote`, `coverageStatus`, `sourceLocator` | `describesETF`, `hasDimension`, `supportedBy`; `hasEntry` → Entry (inverse `inSnapshot`) |
| `AllocationEntry` | `etf:AllocationEntry` | `weightFraction` | `inSnapshot`, `usesCategory` |

### The two shared columns

The earlier draft split `BaseCurrency` into `portfolioCurrency` and `fundCurrency`,
and `WeightFraction` into `holdingWeight` and `declaredWeight`. That split was
semantically attractive and practically wrong: the accepted ABox writes one
predicate per column, so the split properties would have carried no data at all,
and every restriction written on them would have been vacuous.

The ontology therefore declares one property per shared column, with a union
domain:

- `etf:baseCurrency` on `Portfolio` and `ETF`. The subject class disambiguates a
  portfolio's accounting currency from a fund's denomination.
- `etf:weightFraction` on `Holding` and `AllocationEntry`. On a holding it is the
  share of that portfolio; on an entry it is the declared share of the disclosed
  basket.

The cost is stated rather than hidden: because `weightFraction` serves both roles,
only the generic `fibo:hasWeight` is claimed as a super-property, and
`fibo:hasFractionalInterest` is not claimed for a holding any more. A reader who
needs the stronger ownership reading must look at the class, not the predicate. If
the column is ever split, the alignment can be tightened again.

## 3. Association classes

`Holding` and `AllocationEntry` are not many-to-many link tables with a payload
bolted on; they are the two places where the model stores a quantity that belongs
to a relationship, and in the holding's case also a date. Both are kept as full
classes:

- `etf:Holding` specialises `fibo:Holding`, carries `weightFraction`, and keeps
  `holdingAsOfDate` independent of any allocation date. A holding and a disclosure
  can be dated differently and both must survive.
- `etf:AllocationEntry` specialises `fibo:WeightedBasketConstituent`, carries
  `weightFraction`, and points at exactly one snapshot and one category.

Collapsing either into a plain object property would lose the weight (and the date),
which is the whole reason the relation exists. Owl cannot state a property of a
property, so reification into a class is the only correct option here.

## 4. Constraint by constraint: OWL or explicit

This table is the deliverable the task asks for: which rules the ontology
expresses, and which ones only an explicit check can enforce. The reasons are
aggregation, a closed value set, or a uniqueness constraint that names a parent.

| Constraint in the accepted schema | Where it lives | Reason |
| --- | --- | --- |
| `PK_*` primary keys | `recordId` on every individual; not an identity axiom | The surrogate is a local handle. See `namespace_and_identity.md`, section 3. |
| `FK_*` referential integrity | object properties with `rdfs:domain`/`rdfs:range` | A graph has no dangling reference: a triple either exists or it does not. |
| NOT NULL columns | explicit check, plus cardinality restrictions in the ontology | An open world reads a missing value as unknown, not as a violation. `graph_validation.REQUIRED_BY_CLASS` restates each NOT NULL slot. |
| `UK_Customer_CustomerNumber` | `owl:hasKey` on `etf:Customer` | Clean single-column key. |
| `UK_ETFProvider_Registration` | `owl:hasKey` on `etf:ETFProvider` (two columns) | Clean composite key with no parent reference. |
| `UK_AllocationDimension_DimensionName` | `owl:hasKey` on `etf:AllocationDimension` | Clean single-column key. |
| The two `UK_ETFIdentifier` indexes | `owl:hasKey` on `etf:ETFIdentifier` (scheme, value, exchange) | The database splits it into two partial indexes; the graph states one key over all three, with the exchange context absent for an ISIN. Absence is not a value, so the key still discriminates. |
| `UK_Portfolio_CustomerReference` | explicit duplicate check | `owl:hasKey` over `ownedBy` would assert individual equality across parents, which is stronger than per-customer uniqueness. |
| `UK_Holding_PortfolioETFDate` | explicit duplicate check | Same reason; the key names two objects and a literal. |
| `UK_SourceDocument_UrlRetrieved` | explicit duplicate check | Same reason; one literal pair, still parent-free but the URL is long and the pair is not expressible as a key without reading the literal. |
| `UK_ClassificationScheme_KnownVersion` | explicit duplicate check | The index applies only when `Version` is not null, so the graph tolerates one unversioned edition per authority and name and refuses a second. |
| `UK_AllocationCategory_ContextLabel` | explicit duplicate check | Three columns, one of which is an object reference. |
| `UK_AllocationSnapshot_DisclosureBlock` | explicit duplicate check over `describesETF`, `hasDimension`, `allocationAsOfDate`, `supportedBy`, `sourceLocator` | Five columns spanning three objects and two literals; the clearest case for an explicit rule. |
| `UK_AllocationEntry_SnapshotCategory` | explicit duplicate check | Two object references. |
| `CK_*` nonempty-text and shape checks | explicit check for the identifier shapes, permit-list checks for the closed sets | A regular expression on a literal is not expressible in OWL; only the datatype can be stated. |
| `CK_AllocationDimension_DimensionName IN ('Sector','Geography')` | explicit check | A closed value set needs enumerated individuals, which would put instance data into the schema file. |
| `CK_ETFIdentifier_Scheme IN ('ISIN','Ticker')` | explicit check, plus documented ISIN and ticker shapes | Same reason, and the shape rule is a pattern. |
| `CK_AllocationSnapshot_CoverageStatus` | explicit check | Same reason. |
| `CK_Holding_WeightFraction BETWEEN 0 AND 1` and the entry equivalent | `xsd:double` range declaration plus explicit range check | OWL can state the datatype; a numeric facet is not portable across reasoners, so the interval is checked explicitly. |
| `TR_AllocationEntry_Dimension_Insert/Update`, `TR_AllocationSnapshot_Dimension_Update`, `TR_AllocationCategory_Dimension_Update` | property chain `hasEntry · usesCategory · hasDimension ⊑ hasDimension`, plus explicit dimension comparison | The four triggers keep an entry's category dimension equal to its snapshot's. The chain axiom *entails* the equality, but an open world plus no `owl:AllDifferent` on dimension individuals means a contradiction is invisible unless a reasoner runs with distinctness. The explicit check is therefore kept, and this pair of artefacts is the clearest example of why both layers are needed. |
| Complete-snapshot total equals one within 0.005 | explicit only | Aggregation over an open-ended membership set. OWL has no sum. |
| `CapturedFileRef` resolves to an existing file inside the root | explicit only | Filesystem fact, outside the graph. |

### Which attributes get a cardinality restriction

Every object participation carries a restriction. For scalar columns the rule is
deliberately narrower: a restriction is asserted only where the column carries
identity or drives a rule — `customerNumber`, `label`, `contextKey`,
`coverageStatus`, and the capture triple `url`, `retrievedAt`, `capturedFileRef`,
plus `weightFraction` and the two as-of dates. Descriptive text such as `basisNote`,
`sourceLocator`, `legalName` or `fundName` carries none, because the restriction
would restate NOT NULL without telling a reader anything that `REQUIRED_BY_CLASS`
does not already enforce at load time. The file therefore holds 26 restrictions
across nine classes, and a reader looking for the other required slots finds them
in the explicit table rather than in the ontology. This is the one place where the
two layers divide a NOT NULL column between them, and it is a stated policy rather
than an accident of who wrote which axiom.

`graph_validation.py` publishes the two lists as `OWL_ENFORCED_RULES` and
`EXPLICIT_RULES` and prints them with `--rules`, so the split is reviewable without
reading the code.

## 5. What the graph deliberately does not do

The ontology asserts no `owl:AllDifferent` on dimension individuals, no individuals
for `Sector` and `Geography`, and no dated individual data of any kind. Adding
dimension individuals would make the dimension-mismatch case detectable by a reasoner
alone, but it would move instance data into the schema file and make the TBox depend
on the current domain of dimensions. The division of labour we chose is: the TBox
states what must hold, the ABox holds what is observed, and `graph_validation`
checks the arithmetic and the closed sets that neither can express. That position
is argued in the report rather than assumed.

Two related omissions:

- **No inverse materialisation by the backend.** The ABox stores one direction per
  relationship, the foreign-key direction. The ontology declares the five inverse
  pairs; rdflib performs no reasoning, so `graph_validation` closes each pair
  in-memory before checking and the bridge does the same for a candidate store. Without
  that step an at-least-one rule stated on `hasEntry` would fire on a valid ABox that
  stores `inSnapshot`.
- **No reasoner.** Loading the TBox into the backend stores axioms; it activates
  nothing. Every rule that needs closure or counting is therefore restated explicitly.

## 6. Consistency with the relational validator

`dal.models.semantic.graph_validation.scheme_context` and `disclosure_context`
reproduce `dal.schema_validation.scheme_context` and `disclosure_context` byte for
byte, and `tests/test_semantic_ontology.py` asserts that equality directly. The two
layers therefore agree on what a context key is, which is the only cross-layer
invariant that cannot be recovered by inspection of either model alone. The total
tolerance and the `1e-12` floating-point guard are also copied rather than
reinvented, so a value that passes one layer cannot fail the other by arithmetic
accident.
