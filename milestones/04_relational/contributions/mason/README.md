# Mason Li — Milestone 4 contribution

Owner of the database connection/driver, parameterized SQL operations,
representative seed data, analytical queries, quickstart and reproducibility,
and co-author of the architecture figure and final report assembly. Prepared
with AI assistance under the manual's policy **D: AI Task Completion, Human
Evaluation**; the human author reviewed and executed every check below.

## Data approach: fully synthetic

The demonstration is **fully synthetic**. Every customer, provider, source
identity, captured file, classification example, label and weight is
fictional. Source URLs use the reserved `example.invalid` domain and are not
real addresses; the three files in `data/raw/` are plain-text placeholders
with `.pdf` names, not issuer documents. This removes the earlier mismatch
between real provider identities and unsupported synthetic weights. The
executable `seed_data.py` and the reference `seed.sql` produce identical
logical dumps.

## Deliverables

| Artifact | Purpose |
| --- | --- |
| `src/dal/database.py` | Connection context manager; enables and verifies `PRAGMA foreign_keys = ON` on every connection; closes/rolls back automatically. |
| `src/dal/repositories.py` | Parameterized search, detail, entries, portfolio, create, update (single and batch), delete functions returning plain dicts. |
| `src/dal/seed_data.py` | Fully synthetic seed loader inside a validated transaction. |
| `src/dal/run_analysis_queries.py` | Runner for the six analytical queries (in-memory or file database). |
| `src/dal/sql/seed.sql` | Human-readable SQL reference, identical to the executable loader. |
| `src/dal/sql/analysis_queries.sql` | Six SELECT/JOIN/aggregate queries. |
| `src/dal/INTERFACE.md` | Interface contract for the Flask UI integration. |
| `quickstart.py` | One-command build/seed with `--queries`, `--serve` and explicit `--reset`. |
| `milestones/04_relational/figures/system_architecture.dot/.png/.pdf` | Layered architecture figure (UI pending; backend complete). |
| `milestones/04_relational/report/mason_query_dml_section.tex` | Report section on queries, DML integrity and reproducibility. |
| `README.md`, `requirements.txt` | Setup, run instructions and dependencies. |

## Review of the latest patch (commit ee672bb)

I pulled and reviewed the latest `main` before continuing and confirmed the
integration fixes:

- A missing entry inside a batch update now raises `NotFoundError` within the
  transaction, so earlier valid changes are rolled back rather than committed.
- Portfolio reads require an explicit `portfolio_id` and
  `holding_as_of_date`; ambiguous customer-only calls raise a clear
  `ValidationError` instead of choosing an arbitrary portfolio or date.
- Disclosure search adds exact `etf_id` / `allocation_dimension_id` filters
  and source identity; details expose classification authority/name/version
  and the captured publisher, title and publication time.
- Database replacement requires an explicit `--reset`; the replacement is
  built in a temporary directory and atomically published, and a failed seed
  preserves the previous file.

## Design notes

- Every query uses placeholders (`?`); no user value is concatenated into
  SQL, so the interface is not SQL-injectable.
- Writes run inside Taimoor's `validated_transaction`, which validates the
  whole proposed database state before COMMIT; a failure rolls back the
  entire unit with no partial rows.
- A category's `ContextKey` includes the source locator, so a snapshot can
  only use categories whose context matches its own capture; this is enforced
  by the transaction validator rather than by interface checks alone.
- Editing one weight in a Complete snapshot can break its total, so the
  repository provides a batch update that keeps the total within the
  documented 0.005 tolerance.
- The fifth query is a diagnostic candidate listing, not a validated
  portfolio exposure calculation; the report section preserves that
  distinction.

## Verification performed

- `python -m unittest discover -s tests -v`: **44 tests pass** (33 schema
  tests and 11 integration regressions).
- From a clean checkout, `python quickstart.py` builds the database and
  reports the expected row counts; all five Complete snapshots sum to 1.0.
- `python quickstart.py --queries` runs all six queries (counts 8, 2, 5, 5,
  5, 17).
- Re-running without `--reset` validates and reuses the existing database;
  `--reset` rebuilds it.
- Empty disclosures, out-of-range weights, deletion of the last entry, bad
  foreign keys, missing batch entries and dimension mismatches are all
  rejected.
- `PRAGMA integrity_check` returns `ok`, `PRAGMA foreign_key_check` returns
  no violations, and the `seed.sql` and `seed_data.py` builds are identical.

## Limits

- The dataset is a fictional demonstration; no record represents a real fund,
  issuer or observation. The 0.005 tolerance remains a provisional,
  configurable policy rather than a source-calibrated value.
- If the team later switches to genuine data, the retained files must be
  replaced with real captures, the values extracted and manually verified,
  and the synthetic/real wording updated consistently across the loader,
  reference SQL and documentation.

## AI-use record

AI assisted with drafting the connection manager, repository functions, seed
data, queries, architecture figure, report section, README and this
contribution note. The human author pulled and reviewed the latest patch, ran
the builds and tests, accepted the working behavior, and takes responsibility
for the final content.
