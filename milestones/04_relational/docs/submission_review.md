# Milestone 4 submission correction and verification record

Baseline: Mason's handoff commit `c5b500843c0f64a0088c765b4ed9da0f480c156c`.
The coordinator requested these corrections after reviewing the uploaded ZIP
against the official Milestone 4 manual. All members are graduate students;
the existing author order is retained. This record describes AI-assisted
corrections and assistant-executed checks, not new personal test claims.

## Corrections

| Review finding | Implemented correction |
| --- | --- |
| Architecture missing from the report; inaccurate connection/call arrows | Embedded a compact diagram of routes calling helpers and DAL functions separately. Routes obtain/pass connections; repository writes invoke the transaction validator. File checks are conditional on `capture_root`. Updated the topology source and screenshot-layer notes. |
| Four complete screenshots shrunk until unreadable | Replaced the montage with larger, explicitly cropped excerpts of search and successful create/update/delete results. All nine original captures, including rejected operations and provenance/portfolio evidence, are bundled as full-resolution image supplements. Their pixels are checked unchanged. |
| Report and README still describe text masquerading as PDFs | Corrected current descriptions to actual readable synthetic PDFs. These illustrate provenance structure and do not verify real issuer observations. Historical evaluations retain their dated baseline descriptions. |
| Dependency/setup instructions incomplete | Added dependency installation, declared ReportLab/Pillow, documented report tools and optional Poppler preview rendering, and added a checked standalone report/package builder. |
| Incomplete final-artifact navigation/licensing information | Linked the report, source/build guide, evidence and submission ZIP. Documented that no project-wide open-source license has been selected; third-party notices remain intact. No new license was assigned to team members' work. |
| No AI citation in the report | Added a tool citation and a concise evaluation disclosure. Taimoor's supplied design critique, Mason's reported human checks and assistant-executed verification remain distinguished. |

The relation/constraint listing retains the same attributes and rules; only
line wrapping and equivalent wording were adjusted for the ACM fonts. The
data model, schema, seed values and application behavior are unchanged. The report preserves the six query purposes, row
counts, scope of Q5 as diagnostic candidates, rollback rules, independent
dates/contexts and provisional 0.005 fraction tolerance.

## Verification

- A fresh virtual environment installed only the declared Python dependencies.
  The full suite passed: 74 tests (33 schema, 11 integration, 30 UI routes).
- Quickstart created the missing database and ran all six analytical queries;
  expected result counts are 8, 2, 5, 5, 5 and 17.
- The synthetic source generator ran with the declared dependencies and wrote
  three actual PDFs to a separate preview directory without replacing the
  retained examples.
- The review of the baseline independently confirmed identical Python/SQL seed
  dumps, SQLite integrity and foreign-key checks, all 17 allocations matching
  the retained PDFs, database reuse and explicit reset. These behaviors were
  not changed by the submission corrections.
- The report builder stages the standalone source tree used in the ZIP and
  compiles LaTeX/BibTeX. It requires exactly three pages, all twelve relations
  on page three, repository hyperlinks on page one, resolved citations and no
  overfull boxes. The final report is visually inspected for readable figures,
  column/page fit and references. The final PDF uses the ACM Libertine,
  Inconsolata and compatible math fonts, rather than fallback body fonts;
  the builder rejects missing-font fallbacks. Figures use standard PDF fonts.
- All nine supplementary PNGs retain the original dimensions, color mode and
  pixels. Only lossless compression changes. The ZIP is checked for corruption
  and includes its own README, LaTeX, bibliography, class/style and figure PDFs.

## Human evaluation and final review

Taimoor supplied the six design judgments recorded in
[taimoor_design_evaluation.md](taimoor_design_evaluation.md). Mason's handoff
and contribution notes report his own integrated reruns. The interface
contribution records the assistant-executed automated, HTTP and clean-checkout
checks separately from these human evaluations.

The team should inspect the final compiled PDF, confirm that the prose reflects
its understanding and submit the correctly named ZIP. No empirical calibration
from real provider sources is claimed or required for this synthetic demo.
