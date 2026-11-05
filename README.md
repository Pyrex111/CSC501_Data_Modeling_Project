# CSC501 Data Modeling Project

**Extending the Financial Industry Business Ontology to Represent Time-Varying Exchange-Traded Fund Allocations**

University of Victoria, CSC501: Algorithms and Data Models, Fall 2026.

Team: Taimoor Shahzad, Mason Li, and M. Shahmeer Ather Kakwan.

## Project scope

We model dated sector and geographic allocation percentages published by ETF providers. The conceptual model separates a customer's dated ETF holding from a provider's dated allocation disclosure, and connects that disclosure to its entries, category meanings and captured source. FIBO and prior GFRO work inform the design. The relational schema is implemented and tested for Milestone 4, together with the data-access layer, a **fully synthetic** demonstration dataset (all identities and weights are fictional) and a Flask web interface over the same operations; the final team report is being assembled. Knowledge-graph implementation and evaluation follow in later project stages.

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
| Layered system architecture figure | [system_architecture.png](milestones/04_relational/figures/system_architecture.png) |
| Compiled team report draft (3 pages) | [main.pdf](milestones/04_relational/report/main.pdf) |
| Mason report section (queries, DML, reproducibility) | [mason_query_dml_section.tex](milestones/04_relational/report/mason_query_dml_section.tex) |
| Demonstration seed data | [seed.sql](src/dal/sql/seed.sql) |
| Analytical queries | [analysis_queries.sql](src/dal/sql/analysis_queries.sql) |
| Mason contribution and AI-use record | [Mason contribution](milestones/04_relational/contributions/mason/README.md) |
| Historical Milestone 2 conceptual ERD | [Milestone 2 ERD](milestones/02_background/figures/etf_allocation_erd.pdf) |
| Milestone 2 compiled report and appendix | [Report PDF](milestones/02_background/submission/2_Background.pdf) |
| Milestone 2 source and submission package | [Source ZIP](milestones/02_background/submission/2_Background_Taimoor_Mason_Shahmeer.zip) |
| Current reviewed Milestone 3 slide | [One-slide PDF](milestones/03_3mt/slides/3_3MT.pdf) |
| Taimoor's Milestone 3 opening | [Edited spoken draft](milestones/03_3mt/contributions/taimoor/opening_edited.md) |
| Milestone descriptions and navigation | [Milestones index](milestones/README.md) |

The current ERD was revised on 30 October 2026 for Milestone 4 preparation. Its second page/tab documents business identity, scoped uniqueness and prototype assumptions. The Milestone 2 ERD remains available as the historical model; the Milestone 3 slide is a simplified view of that earlier design. The current ERD maps to a tested twelve-relation schema with thirteen foreign keys. The data-access layer, demonstration dataset and Flask web interface are now integrated; the assembled team report is the remaining deliverable.

## Repository organization

| Directory | Purpose |
| --- | --- |
| [milestones/02_background](milestones/02_background/README.md) | Literature review, full ERD, compiled report, source package and member contributions |
| [milestones/03_3mt](milestones/03_3mt/README.md) | One-slide talk, spoken drafts and contribution records |
| [milestones/04_relational](milestones/04_relational/README.md) | Revised ERD, relational dictionary, integration/validation evidence and report fragments |
| [src/ui](src/ui/) | Flask routes and HTML templates; no SQL |
| [src/biz](src/biz/) | Business validation, payload construction and error translation |
| [src/dal](src/dal/) | SQL schema, transaction validator, connection manager and parameterized CRUD/lookups |
| [data/raw](data/) | Fully synthetic retained-evidence files (placeholder text, `.pdf` names) |
| [scripts](scripts/) | Non-destructive schema initializer |
| [tests](tests/) | Schema, integration and UI-route tests |

Within each milestone, shared deliverables are separated from member working drafts. The Milestone 2 source ZIP includes LaTeX, bibliography, figures, preserved drafts and build instructions. The existing member folders retain their original names and history.

## Contributions and editing

Each team member should commit substantive work through their own GitHub account. Shared artifact uploads may be made by the coordinator, so file creation and Git commit authorship should be read together with the contribution notes.

Taimoor leads the opening and presentation model visualization for Milestone 3. Shahmeer presents the gap, model and knowledge-graph direction. Mason assembled the slide and revised its layout. The slide is credited to Mason even though this shared PDF is uploaded by Taimoor.

Supplied original drafts and AI-assisted edited versions are labelled separately. Preserve the Milestone 2 and 3 originals for their editing records. Milestone 4 permits AI task completion with human evaluation; its [handoff](milestones/04_relational/docs/milestone4_handoff.md#ai-use-record) records AI assistance and the team's required review and validation.

## Current status

Milestone 2 artifacts are available above. The reviewed Milestone 3 slide and Taimoor's opening are available. [Shahmeer's original and revised scripts](milestones/03_3mt/contributions/shahmeer/) and [Mason's editable slides](milestones/03_3mt/contributions/Mason/) are available in their contribution folders. Taimoor's current Word draft and matching Markdown script are in his Milestone 3 contribution folder. The final Milestone 3 submission ZIP and editing appendix are not yet recorded here.

Milestone 4 now includes the [revised ERD and business identity rules](milestones/04_relational/figures/etf_allocation_erd_revised.pdf), [editable Draw.io source](milestones/04_relational/figures/etf_allocation_erd.drawio), and [team handoff](milestones/04_relational/docs/milestone4_handoff.md). The [schema contribution](milestones/04_relational/contributions/taimoor/README.md) includes DDL, transaction validation, a schema initializer and 33 behavioral tests. The [data-access contribution](milestones/04_relational/contributions/mason/README.md) adds the connection manager, parameterized CRUD, a fully synthetic seed, six analytical queries, an interface contract, an architecture figure and a one-command quickstart. The [UI contribution](milestones/04_relational/contributions/shahmeer/) adds Flask routes, business validation, UI screenshots and 30 route tests. The compiled team report is being finalized.

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
# Start the Flask web interface
python quickstart.py --serve
# Run the full test suite (schema, integration and UI routes)
python -m unittest discover -s tests -v
```

The quickstart creates the database from `schema.sql` when missing and loads seed data inside a validated transaction. Later runs validate and reuse it. Only `--reset` replaces existing data; a failed rebuild preserves the existing file. The database file is not committed (see `.gitignore`). See the [integration contract](milestones/04_relational/docs/schema_integration.md) before adding write operations.

The [3 November evaluation](milestones/04_relational/docs/taimoor_evaluation.md) covered the original 33 schema tests and 11 integration regression tests; the integrated application now adds 30 UI-route tests, for **74 passing tests** in total. Because the dataset is fully synthetic, these checks validate structure and behavior, not real provider observations.

### Step-by-step schema build

```sh
python scripts/create_schema.py --database data/etf_allocations.sqlite3
PYTHONPATH=src python -m dal.seed_data --database data/etf_allocations.sqlite3
PYTHONPATH=src python -m dal.run_analysis_queries data/etf_allocations.sqlite3
```

The initializer creates a new empty database and refuses to overwrite an existing file. The demonstration is fully synthetic: the three `.pdf` files in `data/raw/` are plain-text placeholders, and every identity and weight is fictional, so no record is presented as a real observation, date, identifier or classification edition. If the team later switches to sourced data, the retained files must be replaced with genuine captures, the values extracted and manually verified, and the synthetic/real wording updated consistently across the loader, reference SQL and documentation.
