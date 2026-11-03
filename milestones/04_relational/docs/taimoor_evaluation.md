# Taimoor: model, schema and integration evaluation

Evaluation date: 3 November 2026. Repository baseline: `main` commit
`290b9caf28267184b573b5929a908b594e7a9b68` (includes Taimoor's supplied design evaluation).
This record covers the follow-up technical work for Taimoor's model/schema
responsibilities. This correction set implements the verified integration fixes
on that baseline. It does not assert either teammate's approval of interface changes.

AI performed the inspection, executed the checks and drafted the corrections.
Taimoor's supplied design decisions are already recorded in
[taimoor_design_evaluation.md](taimoor_design_evaluation.md), committed in the
baseline above. That record is preserved unchanged. This separate technical
integration record supplements it with corrections and automated evidence;
it does not attribute automated execution to Taimoor.

## What was evaluated against what

| Evaluated item | Reference / acceptance basis | Observed result |
| --- | --- | --- |
| Revised ERD entity sets and attributes | First tab of `figures/etf_allocation_erd.drawio`, compared with actual SQLite table metadata | Pass: 12 entities and all 50 conceptual attributes are preserved. The 13 relationship FK columns bring the total to 63 columns. No structural ERD change was required. |
| Relationship directions and cardinality | The 26 entity-to-relationship connections and their crow's-foot endpoint styles, compared with FK direction/nullability and parent-minimum behavioral tests | Pass: all 13 relationships map to FKs on the many side. The scheme relationship alone is optional. ETF identifiers and snapshot entries have their parent-side minimums enforced at the validated transaction boundary. |
| Business identities and scoped uniqueness | ERD second tab, mapping document and behavioral tests | Pass: customer reference, owner-scoped portfolio reference, jurisdiction-scoped registration, exchange-scoped ticker, ISIN, dated holdings, captured sources, allocation blocks and categories have the documented rules. Names and email are descriptive. Known and unknown scheme versions remain distinct cases. |
| Column dictionary | `docs/relational_mapping.md`, compared with `PRAGMA table_info` for every relation | Pass: all 63 names, SQL types and semantic nullability match. Generated INTEGER primary keys are treated as mandatory persisted IDs. |
| SQL mapping and naming | Official `4_Relational_Manual.pdf`, especially Sections 4.1–4.3, plus the current ERD | Pass for the inspected schema: generated INTEGER Id per table, PascalCase names, PK_/UK_/FK_ conventions, all 13 FK names/directions and RESTRICT actions, executable fresh DDL. SQLite is an allowed implementation choice. |
| Constraints and model validator | Documented identity, scalar, dimension, context, participation and total rules | Pass: original 33 behavioral tests rerun. SQL/triggers and transaction validation are explicitly distinguished; raw SQL commits can bypass application-level assertions. |
| Data-access operations | `docs/schema_integration.md` and the shared interface in `docs/milestone4_handoff.md` | Local corrections made for batch rollback, portfolio/date selection, exact ETF/dimension filters, and classification/source output fields. Eleven integration checks pass. UI adoption remains to be checked when it exists. |
| Initialization and reproducibility | Manual Sections 4.2/4.6 and integration contract's prohibition on automatic database removal | Fresh initializer passed; repeating it was refused without changing the file hash. Quickstart now reuses existing data and requires explicit `--reset` to replace it; failed replacement preserves the previous file. |
| Demonstration data integrity | Canonical DDL and `validate_database(..., capture_root=project_root)` | Structurally valid: every table populated, no FK violations, integrity_check = ok, five Complete snapshots have valid totals. This is not source-content verification. |
| Demonstration evidence and classification claims | Actual retained capture contents and the handoff's requirement that real observations agree with retained sources | Unresolved: all three `.pdf` files are short text placeholders, not PDFs. Synthetic weights are linked to real provider URLs; the GICS edition/category claims and purported capture times are unsupported by those files. |
| SELECT/JOIN/aggregate and DML examples | Manual Section 4.4 and shared date/context requirements | Six queries execute; repository create/update/delete and rollback paths are exercised. The aggregate is per snapshot. Q5 is now explicitly a diagnostic candidate listing, not a validated portfolio exposure calculation. |
| Taimoor's report fragments | Actual schema/validator and observed test evidence; manual Section 4.7 relation listing | All 12 relations and 63 columns in the listing match the schema in order. Keys/constraints were inspected against the implementation. Main prose now states 33 schema + 11 integration checks and the source/UI limitations. |
| Whole application and submission | Manual Sections 4.5–4.7, plus team ownership plan | Not complete: no UI/business layer at the inspected commit, no end-to-end UI demonstration, and no assembled final ACM report/ZIP. The existing standalone listing preview is historical; this evaluation did not recompile the final three-page team report. |

The current revised ERD and official Milestone 4 manual were the design/course
references. This is not a fresh review of all original lecture slides or a claim
that project-specific choices are instructor-approved. The historical Milestone 2
ERD was not substituted for the current Milestone 4 model.

## Corrections prepared

1. `src/dal/repositories.py`: a missing ID in a batch update now raises inside
   the validated transaction, rolling back earlier changes. Previously, a valid
   edit could commit before result construction raised a TypeError.
2. Portfolio reads now accept an explicit portfolio and holding date. Ambiguous
   customer-only calls fail with a useful validation error rather than choosing
   an arbitrary portfolio or combining dated holdings. Single-portfolio/date
   calls remain supported. Holdings include ETFId and the selected date remains
   visible independently of any disclosure date.
3. Disclosure search adds exact ETF/dimension ID filters and source identity;
   details expose classification authority/name/version and the captured source's
   publisher, title and publication time. Offering provider and publisher are
   separate roles. Representative ticker selection is deterministic and search
   results include its exchange.
4. `quickstart.py` now requires explicit reset before replacing data, builds a
   replacement before publishing it, and preserves the old file if seeding fails.
   The in-memory analytical runner uses the same validated Python loader as the
   quickstart instead of executing the reference seed SQL with raw commits.
5. Analytical output retains more context/source/date fields. Q5's candidate
   products are labelled diagnostic; it still lists historical candidates and
   does not choose a suitable disclosure or establish equivalent category meanings.
   No validated portfolio-total capability is claimed.
6. README, integration notes, contribution/evidence records and Taimoor's report
   prose now describe the local changes and observed limitations.

The canonical DDL, transaction validator, ERD and column dictionary were retained.
The revised portfolio interface and Q5 column rename should be reviewed with
Mason and Shahmeer before integration. No teammate approval is asserted here.

## Executed checks

Environment: Python 3.12.14, linked SQLite 3.53.1.

```sh
python -m unittest discover -s tests -v
python scripts/create_schema.py --database <new-temporary-database>
python quickstart.py --reset
python quickstart.py --queries
```

- **44 tests passed**, zero failures/errors: 33 original schema tests plus 11
  integration regressions. Tests use fictional fixtures, not verified fund data.
- Fresh schema produced 12 empty tables. A second initializer call was refused;
  the existing database's SHA-256 remained unchanged.
- Explicit quickstart rebuild succeeded; the next CLI run reused the database.
  A regression test also verifies that a failed seed cannot destroy the prior file.
- In-memory and on-disk seed builds produced identical logical dumps.
- Seed validation passed; `PRAGMA integrity_check` returned `ok` and
  `PRAGMA foreign_key_check` returned no rows.
- Query result counts in Q1–Q6 order: **8, 2, 5, 5, 5, 17**. Execution confirms
  SQL behavior, not the truth of observations or semantic equivalence of labels.
- Draw.io/XML and SQLite metadata were compared directly for entity attributes,
  relationship directions, FK optionality, dictionary types/nullability, named
  PKs/FKs and the complete relation listing.

| Relation | Seed rows |
| --- | ---: |
| Customer | 2 |
| Portfolio | 2 |
| Holding | 5 |
| ETFProvider | 2 |
| ETF | 3 |
| ETFIdentifier | 6 |
| SourceDocument | 3 |
| AllocationDimension | 2 |
| ClassificationScheme | 2 |
| AllocationCategory | 13 |
| AllocationSnapshot | 5 |
| AllocationEntry | 17 |

## Retained assumptions and limits

The supplied design evaluation retains the identification/context structure and
the provisional tolerance. The following implementation assumptions and limits
remain documented; this correction set does not alter the design decisions:

- Single bank, individual customers, one sampled offering provider and one
  primary captured source per allocation snapshot; one ETF fund/share class per record.
- A category label is unique within its dimension/context; different contexts
  cannot be equated merely because labels or codes match.
- A known authority/name/version permits a scheme token only when supported by
  evidence. Unknown editions retain NULL and disclosure-local context. The
  validator checks each used category's token; it does not prove a classification
  claim or cross-category/cross-fund semantic compatibility.
- Complete totals use the inclusive 0.005 fraction tolerance. Partial/Unknown
  disclosures and sampled holdings need not sum to one. Zero weights are allowed.
- UTC timestamps have six fractional digits; identity text uses case-sensitive
  comparisons; generated IDs are internal and may be reused after deletion.
- Identifier/country/currency checks validate formats, not external registry
  assignments. Retained-file checks validate location/existence, not authenticity.

## Remaining integration and human work

- **Mason / data evidence:** replace placeholders with genuine captures and
  evidence-supported allocations/classifications, or isolate a fully synthetic
  demo with synthetic captures/source identities. Do not present the current
  seed's numeric values, edition codes or capture times as verified observations.
- **Shahmeer / application:** integrate the corrected outputs and explicit
  portfolio/date choices; demonstrate search/create/update/delete with friendly
  errors, separate observation dates and visible category/source context.
- **Taimoor / follow-up:** the supplied design evaluation is recorded. Review
  the integration corrections and updated report explanation separately, keeping
  the tolerance provisional until genuine source precision supports it. A local
  walkthrough becomes useful when the UI exists; the automated checks above
  were run by the assistant.
- **Team / submission:** run the integrated application from a clean checkout,
  review screenshots/architecture and report accuracy, compile exactly two ACM
  text pages plus the relation page, and inspect the final source/PDF ZIP and
  AI-use/contribution disclosures.

Status: the model/schema technical review and current DAL integration review
are complete with the documented corrections and evidence. Taimoor's supplied design
evaluation is preserved. Teammate integration review, real-source demonstration
evidence and final UI/report/package verification remain open.
