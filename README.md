# CSC501 Data Modeling Project

**Extending the Financial Industry Business Ontology to Represent Time-Varying Exchange-Traded Fund Allocations**

University of Victoria, CSC501: Algorithms and Data Models, Fall 2026.

Team: Taimoor Shahzad, Mason Li, and M. Shahmeer Ather Kakwan.

## Project scope

We model dated sector and geographic allocation percentages published by ETF providers. The conceptual model separates a customer's dated ETF holding from a provider's dated allocation disclosure, and connects that disclosure to its entries, category meanings and captured source. FIBO and prior GFRO work inform the design. The relational schema is implemented and tested for Milestone 4, together with the data-access layer and a validated demonstration dataset; the Flask UI and final team report remain pending. Knowledge-graph implementation and evaluation follow in later project stages.

## Start here

| Artifact | Location |
| --- | --- |
| Current revised conceptual ERD and business identity rules, PDF | [Milestone 4 ERD](milestones/04_relational/figures/etf_allocation_erd_revised.pdf) |
| Editable current ERD, diagrams.net | [Milestone 4 ERD source](milestones/04_relational/figures/etf_allocation_erd.drawio) |
| Executable relational schema | [schema.sql](src/dal/sql/schema.sql) |
| Relational mapping and column dictionary | [Model dictionary](milestones/04_relational/docs/relational_mapping.md) |
| Schema integration and transaction rules | [Integration contract](milestones/04_relational/docs/schema_integration.md) |
| Model, implementation and integration evaluation | [3 November evaluation](milestones/04_relational/docs/taimoor_evaluation.md) |
| Taimoor's supplied design decisions | [Design evaluation](milestones/04_relational/docs/taimoor_design_evaluation.md) |
| Milestone 4 model changes, responsibilities and implementation plan | [Team handoff](milestones/04_relational/docs/milestone4_handoff.md) |
| One-command build and seed | [quickstart.py](quickstart.py) |
| Demonstration seed data | [seed.sql](src/dal/sql/seed.sql) |
| Analytical queries | [analysis_queries.sql](src/dal/sql/analysis_queries.sql) |
| Mason contribution and AI-use record | [Mason contribution](milestones/04_relational/contributions/mason/README.md) |
| Historical Milestone 2 conceptual ERD | [Milestone 2 ERD](milestones/02_background/figures/etf_allocation_erd.pdf) |
| Milestone 2 compiled report and appendix | [Report PDF](milestones/02_background/submission/2_Background.pdf) |
| Milestone 2 source and submission package | [Source ZIP](milestones/02_background/submission/2_Background_Taimoor_Mason_Shahmeer.zip) |
| Current reviewed Milestone 3 slide | [One-slide PDF](milestones/03_3mt/slides/3_3MT.pdf) |
| Taimoor's Milestone 3 opening | [Edited spoken draft](milestones/03_3mt/contributions/taimoor/opening_edited.md) |
| Milestone descriptions and navigation | [Milestones index](milestones/README.md) |

The current ERD was revised on 30 October 2026 for Milestone 4 preparation. Its second page/tab documents business identity, scoped uniqueness and prototype assumptions. The Milestone 2 ERD remains available as the historical model; the Milestone 3 slide is a simplified view of that earlier design. The current ERD maps to a tested twelve-relation schema with thirteen foreign keys. The data-access layer and demonstration dataset are now integrated; the Flask UI and the final team report remain to be completed.

## Repository organization

| Directory | Purpose |
| --- | --- |
| [milestones/02_background](milestones/02_background/README.md) | Literature review, full ERD, compiled report, source package and member contributions |
| [milestones/03_3mt](milestones/03_3mt/README.md) | One-slide talk, spoken drafts and contribution records |
| [milestones/04_relational](milestones/04_relational/README.md) | Revised ERD, relational dictionary, integration/validation evidence and report fragments |
| [src/dal](src/dal/) | SQL schema, transaction validator, connection manager and parameterized CRUD |
| [data/raw](data/) | Captured issuer documents (currently placeholders to be replaced) |
| [scripts](scripts/) | Non-destructive schema initializer |
| [tests](tests/) | Synthetic schema/transaction tests |

Within each milestone, shared deliverables are separated from member working drafts. The Milestone 2 source ZIP includes LaTeX, bibliography, figures, preserved drafts and build instructions. The existing member folders retain their original names and history.

## Contributions and editing

Each team member should commit substantive work through their own GitHub account. Shared artifact uploads may be made by the coordinator, so file creation and Git commit authorship should be read together with the contribution notes.

Taimoor leads the opening and presentation model visualization for Milestone 3. Shahmeer presents the gap, model and knowledge-graph direction. Mason assembled the slide and revised its layout. The slide is credited to Mason even though this shared PDF is uploaded by Taimoor.

Supplied original drafts and AI-assisted edited versions are labelled separately. Preserve the Milestone 2 and 3 originals for their editing records. Milestone 4 permits AI task completion with human evaluation; its [handoff](milestones/04_relational/docs/milestone4_handoff.md#ai-use-record) records AI assistance and the team's required review and validation.

## Current status

Milestone 2 artifacts are available above. The reviewed Milestone 3 slide and Taimoor's opening are available. [Shahmeer's original and revised scripts](milestones/03_3mt/contributions/shahmeer/) and [Mason's editable slides](milestones/03_3mt/contributions/Mason/) are available in their contribution folders. Taimoor's current Word draft and matching Markdown script are in his Milestone 3 contribution folder. The final Milestone 3 submission ZIP and editing appendix are not yet recorded here.

Milestone 4 preparation now includes the [revised ERD and business identity rules](milestones/04_relational/figures/etf_allocation_erd_revised.pdf), [editable Draw.io source](milestones/04_relational/figures/etf_allocation_erd.drawio), and [team handoff](milestones/04_relational/docs/milestone4_handoff.md). The [schema contribution](milestones/04_relational/contributions/taimoor/README.md) now includes DDL, transaction validation, a schema initializer and 33 passing behavioral tests. The [data-access contribution](milestones/04_relational/contributions/mason/README.md) adds the connection manager, parameterized CRUD functions, a validated seed dataset, six analytical queries and a one-command quickstart. The final team report remains pending.

## Run the application

Requires Python 3.10+ linked to SQLite 3.37.0+. From the repository root:

```sh
python -c "import sqlite3; print(sqlite3.sqlite_version)"
# Create the demo database if missing; otherwise validate and reuse it
python quickstart.py
# Also run the six analytical queries
python quickstart.py --queries
# Explicitly replace existing data with a freshly validated demo seed
python quickstart.py --reset
# Run the behavioral test suite
python -m unittest discover -s tests -v
```

The quickstart creates the database from `schema.sql` when missing and loads seed data inside a validated transaction. Later runs validate and reuse it. Only `--reset` replaces existing data; a failed rebuild preserves the existing file. The database file is not committed (see `.gitignore`). See the [integration contract](milestones/04_relational/docs/schema_integration.md) before adding write operations.

The [3 November evaluation](milestones/04_relational/docs/taimoor_evaluation.md) reran the original 33 tests and added 11 integration regression tests: **44 passed**. It records local corrections and the remaining source-evidence, UI and final-report dependencies. Structural validation of seed data does not verify real provider observations.

### Step-by-step schema build

```sh
python scripts/create_schema.py --database data/etf_allocations.sqlite3
PYTHONPATH=src python -m dal.seed_data --database data/etf_allocations.sqlite3
PYTHONPATH=src python -m dal.run_analysis_queries data/etf_allocations.sqlite3
```

The initializer creates a new empty database and refuses to overwrite an existing file. All seed weights are synthetic. The three `.pdf` files in `data/raw/` are text placeholders, so the current records do not verify real observations, dates, identifiers or classification editions. For sourced demonstrations, replace them with genuine retained captures and load evidence-supported values. Alternatively, isolate a fully synthetic demonstration with clearly synthetic source identities; do not cite a real provider capture as evidence for fabricated allocations.
