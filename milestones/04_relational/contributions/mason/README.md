# Mason Li — Milestone 4 contribution

Owner of the database connection/driver, parameterized SQL operations,
representative seed data, analytical queries, quickstart and reproducibility.
Prepared with AI assistance under the manual's policy **D: AI Task
Completion, Human Evaluation**; the human author reviewed and executed every
check below.

## Deliverables

| Artifact | Purpose |
| --- | --- |
| `src/dal/database.py` | Connection context manager; enables and verifies `PRAGMA foreign_keys = ON` on every connection; closes/rolls back automatically. |
| `src/dal/repositories.py` | Parameterized search, detail, portfolio, create, update (single and batch), delete functions returning plain dicts. |
| `src/dal/seed_data.py` | Seed loader that inserts the demo dataset inside a validated transaction. |
| `src/dal/run_analysis_queries.py` | Runner for the six analytical queries. |
| `src/dal/sql/seed.sql` | Human-readable SQL reference for the seed data. |
| `src/dal/sql/analysis_queries.sql` | Six SELECT/JOIN/aggregate queries. |
| `quickstart.py` | One-command fresh build and seed, with `--queries` and `--serve` options. |
| `README.md`, `requirements.txt` | Setup, run instructions and dependencies. |

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

## Verification performed

- Taimoor's 33 behavioral tests pass (`python -m unittest discover -s tests`).
- `python quickstart.py` rebuilds the database from scratch and reports the
  expected row counts; all five Complete snapshots sum to 1.0.
- Empty disclosures, out-of-range weights, deletion of the last entry, bad
  foreign keys and dimension mismatches are all rejected.
- `PRAGMA integrity_check` returns `ok` and `PRAGMA foreign_key_check`
  returns no violations.

## Limits

- All `WeightFraction` values are synthetic; the files in `data/raw/` are
  placeholders and must be replaced with the real captured PDFs, after which
  the weights must be extracted and verified manually.
- Provider registration numbers are labelled placeholders; the ISINs should
  be re-checked against the captured documents.

## AI-use record

AI assisted with drafting the connection manager, repository functions, seed
data, queries, README and this contribution note. The human author ran the
builds and tests, accepted the working behavior, corrected the seed entry
point and context handling, and takes responsibility for the final content.
