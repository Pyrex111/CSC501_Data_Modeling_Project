# M5 integration contract: backend and ontology integrated

Prepared by AI for Taimoor's review, 20 November 2026. This does not assert team
agreement at that time. Update, 24 November: Mason's v1.1.0 ontology follows these
terms, and the backend startup now attaches his native validator. Accepted M4
baseline: `a00c0052289bc5acce17ad1b57f4d84832abda14`.

## Proposed terms and identity

Ontology namespace: `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/ontology#`.
Entity resources: `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/resource/{Entity}/{Id}`.
Data graph: `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/graph/data`.
Ontology graph: `https://github.com/Pyrex111/CSC501_Data_Modeling_Project/graph/ontology`.

These project IRIs identify resources; GitHub does not automatically serve RDF
at them. No claim of content negotiation or globally dereferenceable linked-data
hosting is made. Future live imports need an agreed ID allocation policy; the
present IDs are stable for the migrated demonstration records. New records use
MAX(Id)+1, matching the M4-style local record convention. Deleting the highest-ID
entry can therefore permit later ID/IRI reuse. These provisional IRIs must not be
published as permanent external identities until Mason and Taimoor agree a
non-reusing allocation policy or a different resource-identity design.

Every accepted entity has the same class name and a typed `recordId`. A scalar
column uses its lower-camel-case name; relationships use the centralized mapping
in `vocabulary.py` and the generated [proposal](vocabulary_proposal.json).
No FK is serialized as a second integer datatype property: it becomes an IRI edge.
NULL means an omitted property, not an empty string, `Unknown` resource or dummy value.
Dates are xsd:date, source times xsd:dateTime, record IDs xsd:integer, fractions
xsd:double and other scalar fields xsd:string. The adapter restores M4's six-digit
UTC timestamp spelling after Oxigraph normalizes redundant zeroes; this is needed
to reconstruct accepted disclosure-local ContextKeys consistently.

Mason aligned the ontology to the committed vocabulary; see `backend_alignment.md`.
`hasDimension` is shared by categories and snapshots; multiple
RDFS domain statements would imply an intersection, so its domain needs deliberate
modeling (for example a union or suitable superclass), not two accidental domains.
Do not declare an `owl:hasKey` on recordId alone globally or treat OWL restrictions
as closed-world required-field checks. FIBO subclass/subproperty decisions belong
to Mason's ontology; see `fibo_alignment.md`.

## Application interface for Shahmeer

Use `semantic.repositories` and `semantic.lookups` with a shared GraphDatabase
instead of `dal.repositories`/`dal.lookups` with a SQLite connection. Error classes
are the existing RepositoryError/ValidationError/NotFoundError/BusinessRuleError.

Use the integrated startup once when creating the application:

```python
from semantic.runtime import open_graph_database
graph = open_graph_database('data/semantic_store')
```

This binds Mason's native validator with the project capture root, validates
existing data, and loads the committed ontology. Reuse this same instance across
requests. The factory does not seed data or start Flask: run the quickstart first.
All graph repository function signatures below are unchanged.

| Function | Inputs / result |
| --- | --- |
| `search_disclosures` | Same ticker/dimension/date filters and exact ETF/dimension IDs; same list-of-dicts result |
| `get_disclosure_detail` | Snapshot ID; source/publisher/coverage/context plus Entries with optional scheme fields |
| `get_allocation_entries` | Snapshot ID; same entry dictionaries |
| `get_customer_portfolio` | Customer number, explicit portfolio/date when ambiguous; same customer/portfolio/holdings dictionary |
| `create_disclosure` | Same payload including Entries; returns saved detail after successful validation/commit |
| `update_entry_weight` / `update_weights_batch` | Existing IDs and fractions; complete totals must remain valid |
| `delete_entry` | Entry ID; rejects invalid remaining totals or final-entry deletion |
| `list_etfs`, `list_dimensions`, `list_source_documents`, `list_categories`, `list_customers` | Same form lookup result dictionaries |
| `list_customer_portfolios`, `list_holding_dates` | Same arguments and results |

User text is serialized using RDF Literal/NamedNode handling, not interpolated
unescaped. IDs are checked as integers. The query text/term names are application
code, not accepted directly from forms. Preserve the existing business-layer form
validation. Search label matches do not assert semantic equivalence; Q5 candidates
do not select compatible disclosure dates or produce a portfolio exposure total.

## Mason's shared validation hook

```python
from semantic.store import GraphDatabase

def validate_graph(candidate_store):
    # Inspect the complete proposed state through SPARQL or a graph validator.
    # Raise dal.schema_validation.ModelIntegrityError with an actionable message
    # on any failure. Return None on success. Do not mutate the candidate.
    ...

graph = GraphDatabase('data/semantic_store', validator=validate_graph)
```

The ellipsis above is an interface illustration. Mason's implemented adapter is
`dal.models.semantic.backend_bridge.make_backend_validator(capture_root=...)`;
the shared factory shown above always attaches it.
Use the proposed DATA_GRAPH for ABox checks; TBox is separate. The initial backend
always runs a strict temporary M4 parity validator, then invokes the supplied
callback. That bridge decodes every mapped RDF fact into an ephemeral accepted
SQLite schema and runs its keys/checks/dimension/context/minimum-child/total rules.
It rejects unknown ABox predicates, unsupported types, multivalued scalar fields,
wrong literal types and missing/wrong-class reference targets rather than dropping
facts. It is useful migration protection, **not Mason's native graph validation**.
Mason has supplied native graph rules and tests. The bridge is retained as
additional migration protection; this integration does not retire it. Nine runtime
tests include native-only rejection checks with the bridge mocked out within those
tests, so success cannot be attributed solely to the SQL checks.

Write order: acquire shared RLock -> copy current dataset -> execute proposed
SPARQL against candidate -> inspect candidate -> validate -> compute exact data
delta -> one transactional Store.update -> release lock. IDs are allocated while
holding that lock. Candidate/validator errors cannot change the persistent graph.
Application operations may not alter the ontology or other named graphs. Validators
must return None and remain read-only; False/True results or mutation are rejected.

Scope: a single process owns one writable RocksDB store. This does not implement
distributed coordination, public SPARQL updates, multiple worker processes or OWL
reasoning. Direct private `_store` updates can bypass the application boundary,
just as raw commits bypassed the M4 validator; UI code must not perform them.

## Integration order and acceptance

1. Complete: Mason aligned the RDF/XML ontology and native validator to the backend.
2. Complete: the quickstart and CRUD demo use integrated startup; six queries still
   match SQL, startup/reuse and rejected-write rollback pass.
3. Shahmeer connects search and detail first, then portfolio/form lookups and
   create/update/delete; preserve distinct dates and friendly validation messages.
4. Verify rejected writes against the actual integrated UI, collect screenshots
   and architecture, rerun query parity and review the final three-page report.

The suite now has 160 tests (74 M4 + 26 backend + 51 ontology + nine runtime), plus
six full-result SQL comparisons. These checks demonstrate backend/ontology
integration, not an integrated semantic UI. See `backend_integration.md`.
