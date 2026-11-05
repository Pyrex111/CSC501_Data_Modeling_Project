# CSC501 Data Modeling Project

**Extending the Financial Industry Business Ontology to Represent Time-Varying Exchange-Traded Fund Allocations**

University of Victoria, CSC501: Algorithms and Data Models, Fall 2026.

Team: Taimoor Shahzad, Mason Li, and M. Shahmeer Ather Kakwan.

## Project scope

We model dated sector and geographic allocation percentages published by ETF providers. The conceptual model separates a customer's dated ETF holding from a provider's dated allocation disclosure, and connects that disclosure to its entries, category meanings and captured source. FIBO and prior GFRO work inform the design. Milestone 4 includes a relational schema, data-access layer, **fully synthetic** demonstration dataset, Flask interface and three-page report. Knowledge-graph implementation and evaluation follow in later project stages.

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
| Compiled team report (3 pages) and build instructions | [main.pdf](milestones/04_relational/report/main.pdf), [report README](milestones/04_relational/report/README.md) |
| Milestone 4 submission ZIP | [4_Relational_Taimoor_Mason_Shahmeer.zip](milestones/04_relational/submission/4_Relational_Taimoor_Mason_Shahmeer.zip) |
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

The current ERD was revised on 30 October 2026 for Milestone 4 preparation. Its second page/tab documents business identity, scoped uniqueness and prototype assumptions. The Milestone 2 ERD remains available as the historical model; the Milestone 3 slide is a simplified view of that earlier design. The current ERD maps to a tested twelve-relation schema with thirteen foreign keys. The integrated application, report and submission package are linked above. Individual review and verification are recorded separately from automated checks.

## Repository organization

| Directory | Purpose |
| --- | --- |
| [milestones/02_background](milestones/02_background/README.md) | Literature review, full ERD, compiled report, source package and member contributions |
| [milestones/03_3mt](milestones/03_3mt/README.md) | One-slide talk, spoken drafts and contribution records |
| [milestones/04_relational](milestones/04_relational/README.md) | Revised ERD, relational dictionary, evaluation, figures, report and submission ZIP |
| [src/ui](src/ui/) | Flask routes and HTML templates; no SQL |
| [src/biz](src/biz/) | Business validation, payload construction and error translation |
| [src/dal](src/dal/) | SQL schema, transaction validator, connection manager and parameterized CRUD/lookups |
| [data/raw](data/raw/) | Three readable synthetic source PDFs; all identities and observations are fictional |
| [scripts](scripts/) | Schema initializer, synthetic PDF/figure generators and report/package builder |
| [tests](tests/) | Schema, integration and UI-route tests |

Within each milestone, shared deliverables are separated from member working drafts. The Milestone 2 source ZIP includes LaTeX, bibliography, figures, preserved drafts and build instructions. The existing member folders retain their original names and history.

## Contributions and editing

Each team member should commit substantive work through their own GitHub account. Shared artifact uploads may be made by the coordinator, so file creation and Git commit authorship should be read together with the contribution notes.

Taimoor leads the opening and presentation model visualization for Milestone 3. Shahmeer presents the gap, model and knowledge-graph direction. Mason assembled the slide and revised its layout. The slide is credited to Mason even though this shared PDF is uploaded by Taimoor.

Supplied original drafts and AI-assisted edited versions are labelled separately. Preserve the Milestone 2 and 3 originals for their editing records. Milestone 4 permits AI task completion with human evaluation; its [handoff](milestones/04_relational/docs/milestone4_handoff.md#ai-use-record) records AI assistance and the team's required review and validation.

## Current status

Milestone 2 artifacts are available above. The reviewed Milestone 3 slide and Taimoor's opening are available. [Shahmeer's original and revised scripts](milestones/03_3mt/contributions/shahmeer/) and [Mason's editable slides](milestones/03_3mt/contributions/Mason/) are available in their contribution folders. Taimoor's current Word draft and matching Markdown script are in his Milestone 3 contribution folder. The final Milestone 3 submission ZIP and editing appendix are not yet recorded here.

Milestone 4 includes the [revised ERD and business identity rules](milestones/04_relational/figures/etf_allocation_erd_revised.pdf), [editable Draw.io source](milestones/04_relational/figures/etf_allocation_erd.drawio), and [team handoff](milestones/04_relational/docs/milestone4_handoff.md). The [schema contribution](milestones/04_relational/contributions/taimoor/README.md) includes DDL, transaction validation, a schema initializer and 33 behavioral tests. The [data-access contribution](milestones/04_relational/contributions/mason/README.md) adds parameterized CRUD, a synthetic seed, six queries and quickstart. The [UI contribution](milestones/04_relational/contributions/shahmeer/readme.md) adds Flask routes, business validation, screenshots and 30 route tests. Eleven additional integration tests bring the suite to 74. The report and submission ZIP are available under **Start here**.

## Run the application

Requires Python 3.10+ linked to SQLite 3.37.0+. From the repository root:

```sh
python -c "import sqlite3; print(sqlite3.sqlite_version)"
# Install the interface and artifact-generation dependencies
python -m pip install -r requirements.txt
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

The initializer creates a new empty database and refuses to overwrite an existing file. The three files in `data/raw/` are actual, readable synthetic PDFs with explicit fictional-data notices and tables matching the seed. They demonstrate the provenance structure, rather than establishing genuine provider observations. To reproduce them from a fresh demo database without overwriting the retained examples:

```sh
python scripts/generate_synthetic_pdfs.py --output-dir tmp/synthetic-preview
```

If the team later switches to sourced data, retain genuine captures, verify the extracted observations, and update the synthetic/real wording consistently. The configurable `0.005` fraction tolerance is a provisional demonstration policy, not a measured provider rounding tolerance.

## Report and submission

With a LaTeX installation containing the ACM `sigconf` dependencies and BibTeX:

```sh
python scripts/generate_report_figures.py
python scripts/build_m4_submission.py
```

The builder compiles in a temporary directory, checks the two-report-page plus one-relation-page structure, and publishes the PDF and self-contained source ZIP only after success. See the [report instructions](milestones/04_relational/report/README.md) and [correction/verification record](milestones/04_relational/docs/submission_review.md). Full-resolution UI captures are included in the ZIP as supplementary image files.

## Citation

Taimoor Shahzad, M. Shahmeer Ather Kakwan, and Mason Li. 2026. *Dated ETF Allocation Disclosures: A Relational Design and Data-Access Layer*. CSC501, University of Victoria. https://github.com/Pyrex111/CSC501_Data_Modeling_Project.

## License and access

No project-wide open-source license has been selected. The repository and submission are available for course evaluation; contact the authors about other reuse. Third-party files, including the ACM LaTeX class and bibliography style, retain their own license notices. This statement does not assign a new license to other team members' work.
