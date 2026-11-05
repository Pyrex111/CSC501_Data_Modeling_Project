# Milestone 4: Solution Design and Implementation, Part I: Relational

Status: schema, data-access layer and a fully synthetic demonstration dataset are integrated with the Flask web interface and pass 74 tests. The conceptual model was revised on 30 October 2026. The official submission deadline is 4 November 2026 AoE.

## Start here

| Artifact | Location |
| --- | --- |
| Revised conceptual ERD and business identity rules, two-page PDF | [figures/etf_allocation_erd_revised.pdf](figures/etf_allocation_erd_revised.pdf) |
| Editable Draw.io source, two tabs | [figures/etf_allocation_erd.drawio](figures/etf_allocation_erd.drawio) |
| Layered system architecture figure | [figures/system_architecture.png](figures/system_architecture.png) |
| Revision explanation, implementation rules and team responsibilities | [docs/milestone4_handoff.md](docs/milestone4_handoff.md) |
| Executable relational schema | [schema.sql](../../src/dal/sql/schema.sql) |
| Relation/column dictionary | [docs/relational_mapping.md](docs/relational_mapping.md) |
| Teammate integration contract | [docs/schema_integration.md](docs/schema_integration.md) |
| Observed schema validation results | [docs/schema_validation_results.md](docs/schema_validation_results.md) |
| Taimoor's supplied design evaluation, 3 November | [docs/taimoor_design_evaluation.md](docs/taimoor_design_evaluation.md) |
| Taimoor's contribution and review guide | [contributions/taimoor/README.md](contributions/taimoor/README.md) |
| Report fragments and relation-list preview | [report/README.md](report/README.md) |
| Historical Milestone 2 model | [Milestone 2 figures](../02_background/figures/) |

Open the Draw.io file in diagrams.net. The first tab is the conceptual ERD; the second explains business identification, scoped uniqueness and implementation rules. The PDF contains the same two views. The official Milestone 4 manual governs the requirements; illustrative samples do not override it.

## Folder organization

- `figures/`: shared model PDF, its editable source, the architecture figure and UI screenshots.
- `docs/`: model revision explanation, assumptions, implementation decisions and team handoff.
- `report/`: assembled three-page report, section fragments, bibliography and the relation/constraint listing.
- `contributions/`: per-member ownership, evaluation and review records.
- `README.md`: artifact navigation and milestone status.

The root-level `src/` now holds the Flask routes (`src/ui`), business validation (`src/biz`) and the data-access layer (`src/dal`); `scripts/` contains a schema-only initializer and `tests/` covers the schema, integration and UI routes. The final submission package is being assembled.

## Model revision

The revision clarifies individual Customer and registered-company ETFProvider records, introduces explicit business references and scoped uniqueness rules, and standardizes attribute names to PascalCase. It retains the twelve entity sets and existing relationships/cardinalities. Holding and AllocationEntry retain the weight/date facts appropriate to their associative roles.

The new business rules are documented prototype assumptions for team review. They are not claims that the instructor specifically required those exact attributes or approved the proposed rules. The [relational mapping](docs/relational_mapping.md) accounts for all fifty conceptual attributes plus thirteen FK columns in twelve relations. Schema/transaction tests pass; the [integration contract](docs/schema_integration.md) distinguishes SQL-enforced rules from application transaction checks.

## Responsibilities

| Member | Main ownership | Expected deliverables |
| --- | --- | --- |
| Taimoor Shahzad | Model and relational schema | Reviewed ERD, relation/column dictionary, executable schema and constraint listing |
| M. Shahmeer Ather Kakwan | UI and business logic | Search/detail views, agreed write operations, validation and UI evidence |
| Mason Li | Data access, sample data and reproducibility | Parameterized SQL functions, sample records, quickstart, README and clean-run verification |
| All members | Report and review | Explanation/evidence for their own work, cross-review, final report/package checks and substantive individual commits |

See the [handoff](docs/milestone4_handoff.md#ownership-and-deliverables) for exact deliverables, acceptance criteria and dependencies.

## Submission status

Available: revised conceptual model, business identity rules, executable schema, relation/column dictionary, shared transaction validator, schema initializer, 74 passing tests (33 schema, 11 integration, 30 UI routes), connection manager, parameterized CRUD and lookups, fully synthetic seed data, six analytical queries, an interface contract, an architecture figure, the Flask application with UI screenshots and the compiled three-page report.

Remaining: final cross-review and the submission ZIP. The report contains two report pages plus one page listing all relations and constraints. The planned package name is `4_Relational_Taimoor_Mason_Shahmeer.zip`.

## AI assistance and evaluation

AI assisted with the model revision, visual exports, handoff and 2 November schema/code/documentation contribution. The [contribution record](contributions/taimoor/README.md#ai-use-and-evaluation-record) distinguishes executed automated checks from pending human evaluation. The Milestone 4 manual classifies the work as **D: AI Task Completion, Human Evaluation**. Team members must critically review the design, validate the implementation and document/cite AI assistance as required. See the [AI-use record](docs/milestone4_handoff.md#ai-use-record).
