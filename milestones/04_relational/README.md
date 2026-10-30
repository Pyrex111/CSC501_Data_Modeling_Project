# Milestone 4: Solution Design and Implementation, Part I: Relational

Status: preparation in progress. The model was revised on 30 October 2026. The official submission deadline is 4 November 2026 AoE.

## Start here

| Artifact | Location |
| --- | --- |
| Revised conceptual ERD and business identity rules, two-page PDF | [figures/etf_allocation_erd_revised.pdf](figures/etf_allocation_erd_revised.pdf) |
| Editable Draw.io source, two tabs | [figures/etf_allocation_erd.drawio](figures/etf_allocation_erd.drawio) |
| Revision explanation, implementation rules and team responsibilities | [docs/milestone4_handoff.md](docs/milestone4_handoff.md) |
| Historical Milestone 2 model | [Milestone 2 figures](../02_background/figures/) |

Open the Draw.io file in diagrams.net. The first tab is the conceptual ERD; the second explains business identification, scoped uniqueness and implementation rules. The PDF contains the same two views. The official Milestone 4 manual governs the requirements; illustrative samples do not override it.

## Folder organization

- `figures/`: shared model PDF and its editable source.
- `docs/`: model revision explanation, assumptions, implementation decisions and team handoff.
- `README.md`: artifact navigation and milestone status.

The runnable application, data and SQL can be implemented in shared root-level `src/` and `data/` directories as described in the handoff. Report sources and the final submission package will be added under this milestone when ready.

## Model revision

The revision clarifies individual Customer and registered-company ETFProvider records, introduces explicit business references and scoped uniqueness rules, and standardizes attribute names to PascalCase. It retains the twelve entity sets and existing relationships/cardinalities. Holding and AllocationEntry retain the weight/date facts appropriate to their associative roles.

The new business rules are documented prototype assumptions for team review. They are not claims that the instructor specifically required those exact attributes or approved the proposed rules. This conceptual model still needs to be mapped into an executable relational schema.

## Responsibilities

| Member | Main ownership | Expected deliverables |
| --- | --- | --- |
| Taimoor Shahzad | Model and relational schema | Reviewed ERD, relation/column dictionary, executable schema and constraint listing |
| M. Shahmeer Ather Kakwan | UI and business logic | Search/detail views, agreed write operations, validation and UI evidence |
| Mason Li | Data access, sample data and reproducibility | Parameterized SQL functions, sample records, quickstart, README and clean-run verification |
| All members | Report and review | Explanation/evidence for their own work, cross-review, final report/package checks and substantive individual commits |

See the [handoff](docs/milestone4_handoff.md#ownership-and-deliverables) for exact deliverables, acceptance criteria and dependencies.

## Submission status

Available: revised conceptual model, business identity rules and implementation handoff.

Pending: relational schema, sample data, SQL operations, application, architecture/UI evidence, reproducibility checks, ACM report and final ZIP. The report must contain two report pages plus one page listing all relations and constraints. The planned package name is `4_Relational_Taimoor_Mason_Shahmeer.zip`.

## AI assistance and evaluation

AI assisted with the model revision, visual exports and handoff. The Milestone 4 manual classifies the work as **D: AI Task Completion, Human Evaluation**. Team members must critically review the design, validate the implementation and document/cite AI assistance as required. See the [AI-use record](docs/milestone4_handoff.md#ai-use-record).
