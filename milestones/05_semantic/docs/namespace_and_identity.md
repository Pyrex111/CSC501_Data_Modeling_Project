# Namespace and Resource Identity Policy

Milestone 5, semantic layer. Owner: Mason Li (ontology and semantic validation),
with AI assistance disclosed in the contribution notes.

This policy fixes the two things the team must agree on before any triple is
written: where terms live, and how an individual is named. Both are load-bearing,
because an identifier that changes breaks every stored query, and one that collides
silently merges two disclosures that should stay apart.

Version 1.1.0 aligns these rules with the accepted graph backend
(`milestone5/taimoor-semantic-backend`, commit `f03f150`). Where the earlier draft
minted business-key IRIs, the accepted ABox already carries record-scoped IRIs;
section 3 records that decision and its cost instead of pretending the two designs
coincide.

## 1. Namespaces

| Prefix | Namespace | Holds |
| --- | --- | --- |
| `etf` | `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/ontology#` | classes, properties (the TBox) |
| `res` | `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/resource/` | individuals (the ABox) |
| `fibo` | `https://spec.edmcouncil.org/fibo/ontology/` | reused FIBO terms, referenced only |
| `cmns` | `https://www.omg.org/spec/Commons/` | reused OMG Commons terms, referenced only |
| `xsd` | `http://www.w3.org/2001/XMLSchema#` | literal datatypes |
| `rdf`, `rdfs`, `owl` | standard | standard vocabulary |

Terms and individuals are kept in separate namespaces on purpose. A hash
namespace for the vocabulary and a path namespace for the data means a mistyped
individual can never be read as a term, and regenerating the ABox cannot
accidentally redefine a class. The backend also writes two named graphs,
`.../graph/data` and `.../graph/ontology`, so a load can replace the TBox without
touching a single instance.

The ontology IRI is `.../ontology` and the file carries `owl:versionInfo`
instead of `owl:versionIRI`. The file ships inside the repository rather than
being dereferenced from a public endpoint, so a second resolvable IRI would add a
minting obligation without a consumer. If the vocabulary is later published, the
version IRI is the natural next step.

### Why FIBO is referenced, not imported

`etf_allocations.owl` contains no `owl:imports`. Every FIBO and Commons class or
property appears as an IRI only, in `rdfs:subClassOf` or as a super-property.

The reason is reproducibility. FIBO is a large modular ontology; importing it
pulls a closure that must resolve over the network, and the marker would then be
unable to open the file offline or after FIBO is reorganised. Referencing the IRI
keeps the file self-contained and keeps the alignment auditable as a written
claim, which is what the report has to defend. A reader with FIBO loaded can still
see the subsumption; a reader without it can still parse and validate the file.

## 2. Datatypes and the two shared columns

Scalar columns map to `owl:DatatypeProperty` with the datatype the accepted ABox
actually carries, which is the type the loader writes for that column.

| Column type | Datatype | Note |
| --- | --- | --- |
| `INTEGER` (including `Id`) | `xsd:integer` | `Id` is exported as `recordId` |
| `REAL` | `xsd:double` | SQLite `REAL` is IEEE-754 binary64 |
| `*Date` | `xsd:date` | |
| `RetrievedAt`, `PublishedAt` | `xsd:dateTime` | UTC; see the lexical note below |
| text, including URL columns | `xsd:string` | URLs are not typed `xsd:anyURI` |

**`REAL` is declared `xsd:double`, not `xsd:decimal`.** The accepted schema stores
weights as SQLite `REAL`, which is an IEEE-754 double, and the accepted ABox writes
them with that datatype. Declaring `xsd:decimal` would have made every stored
weight literal a type mismatch; the earlier decimal draft was reversed for that
reason. The 0.005 tolerance in the relational validator exists precisely because
binary doubles do not sum to one exactly, so the tolerance stays a validation
parameter: no ontology can state an aggregate, and pretending to do so at the
datatype level would hide the real reconciliation.

**URL columns stay plain strings.** `Url`, `WebsiteUrl` and `DefinitionUrl` are
written as untyped literals by the loader. An `xsd:anyURI` range would be the
tighter choice, but it would make the accepted triples ill-typed, so the ontology
declares `xsd:string` and the checks that care about a URL's shape are written
explicitly.

**Date and time lexical forms.** As-of columns are `xsd:date`. The retrieval and
publication columns are `xsd:dateTime` in UTC spelling. rdflib re-serialises a
trailing `Z` as `+00:00` when a literal is parsed, so the validator accepts both
spellings and rejects any non-zero offset; accepting only `Z` would fail on the
same graph depending on which library read it.

**Two columns are shared, so two properties have union domains.** The schema names
`BaseCurrency` in both `Portfolio` and `ETF`, and `WeightFraction` in both `Holding`
and `AllocationEntry`, and the accepted ABox uses one predicate for each. Rather
than invent a second name, the ontology declares one property per shared column with
`owl:unionOf` as its domain; the subject class says which reading applies. `recordId`
likewise has a union domain over the twelve classes.

The weight case has a semantic cost that is stated rather than hidden: a holding's
weight is an ownership fraction, while an entry's weight is a declared share of a
disclosed basket. Because one predicate carries both, only the generic FIBO
`hasWeight` is claimed as a super-property; `hasFractionalInterest` is not, since an
allocation share is not a fractional interest. If the column is ever split, the
stronger alignment becomes available again.

## 3. Resource identifiers are record handles

The accepted rule is:

```
res:{Table}/{Id}
```

Every individual is typed with exactly one class IRI and carries its integer
`recordId`. The IRI is a handle for the migrated row; it is not a business key.
Business identity stays where the relational model already puts it:

| Class | Identity enforced by | Where |
| --- | --- | --- |
| Customer | `owl:hasKey(customerNumber)` | OWL |
| ETFProvider | `hasKey(registrationJurisdiction, registrationNumber)` | OWL |
| ETFIdentifier | `hasKey(identifierScheme, identifierValue, exchangeContext)` | OWL |
| AllocationDimension | `hasKey(dimensionName)` | OWL |
| ETF | no key of its own in the schema; at least one identifier is required | explicit |
| Portfolio | `UK(CustomerId, PortfolioReference)` names a parent | explicit |
| Holding | `UK(PortfolioId, ETFId, HoldingAsOfDate)` names parents | explicit |
| SourceDocument | `UK(Url, RetrievedAt)` | explicit |
| ClassificationScheme | conditional `UK` only when `Version` is not null | explicit |
| AllocationCategory | `UK(AllocationDimensionId, ContextKey, Label)` names a parent | explicit |
| AllocationSnapshot | `UK(ETF, Dimension, AsOfDate, Source, SourceLocator)` names parents | explicit |
| AllocationEntry | `UK(SnapshotId, CategoryId)` names parents | explicit |

Composite keys that name a parent cannot be `owl:hasKey`: a key over an object
property asserts that two individuals are equal, which is stronger than "unique
within the same parent". They are checked explicitly instead, as section 4 of
`ontology_mapping.md` records.

**Why record handles rather than minted business keys.** The backend had already
migrated the accepted synthetic dataset (356 triples) and built its six SPARQL
results and 26 tests on this form; changing it would have meant regenerating the
ABox, the queries and the tests for no gain in the milestone's criteria, which ask
for a documented identifier rule rather than for semantic IRIs. Record handles also
keep the existing integer identifiers that the application and the UI already use.

**The cost, stated plainly.** `recordId` is allocated as `MAX(Id)+1`, so deleting
the highest-numbered record allows its identifier, and therefore its IRI, to be
reused. Two consequences follow:

1. The migrated demonstration IRIs must not be published as permanent external
   identities. The integration contract says the same thing, and this policy
   agrees with it.
2. Within the project, aggregates are append-only: a correction is a new dated
   snapshot or a new capture, never a deletion of the highest row. Where a
   deletion is unavoidable, the identifier is retired rather than recycled.

If the vocabulary is ever exposed outside the repository, the correct fix is a
separate identity layer (a UUID or a monotonically versioned IRI) minted at
publication time, with `recordId` kept as the local handle. That layer is
deliberately not invented here.

**An ETF has no unique key of its own.** Nothing in the accepted schema
distinguishes two funds with the same name from the same provider. Identity
therefore rests on the row plus the identifier set: the explicit "at least one
identifier" rule guarantees that a fund is identifiable through
`identifiesETF`, and the two partial unique indexes on `ETFIdentifier` stop the
same ISIN or ticker+exchange from naming two funds. This is weaker than a
business-key IRI and is one more reason to keep these IRIs local.

## 4. Category identity and the context key

`AllocationCategory` is the one class whose identity is not a single column. The
schema gives it `UK(AllocationDimensionId, ContextKey, Label)` and builds
`ContextKey` out of the classification edition or, when the edition is unknown,
out of the capture itself:

```
scheme:["authority","name","version"]
source:["url","retrievedAt","locator","dimension"]
```

The graph keeps exactly this construction. `graph_validation.py` exposes
`scheme_context` and `disclosure_context`, and the test suite asserts that
`dal.models.semantic.graph_validation.scheme_context` and
`dal.schema_validation.scheme_context` return byte-identical strings for the same
inputs. That test is the guard against the two layers drifting apart: if one side
changes its JSON separators or its prefix, the parity test fails rather than
letting the graph accumulate categories that no longer line up with the database.

The practical consequence is that a label such as `Technology` in the v1 edition
of a sector scheme and the same label in v2 are two resources, and neither merges
with the other, which is what the accepted model intends.

## 5. Provenance obligations

Every observed allocation block keeps four pieces of evidence: the source document
it came from (`supportedBy`), the fund and dimension it describes, the as-of date
it claims, and the locator inside the capture that the weights were read from
(`sourceLocator`). The capture itself is retained and referenced by
`capturedFileRef`.

`capturedFileRef` is a project-relative path. Under the synthetic demonstration
these files are generated PDFs, so the explicit check confirms that the file
exists inside `capture_root` and does not escape it; it does not and cannot confirm
that the file supports the weights. That limitation belongs in the report,
because conflating "the capture exists" with "the numbers are true" is exactly the
provenance error the model is trying to prevent.

## 6. Versioning and change policy

The vocabulary changes in place, with `owl:versionInfo` and the repository history
as the record: 1.0 was the first draft, 1.1.0 is the version aligned to the
accepted backend vocabulary. Individuals are never re-minted once published: a
correction is expressed by adding a new dated snapshot or a new capture, not by
renaming a resource. This is the same discipline the accepted schema enforces by
keeping allocations dated and keyed to their source rather than overwritten.
