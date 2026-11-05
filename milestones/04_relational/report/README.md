# Milestone 4 report and submission

`main.tex` combines the model, query/DML and interface contributions, an
architecture diagram, UI evidence, AI attribution and references. The compiled
`main.pdf` has two report pages followed by one relations/constraints page.
All members are graduate students, so the existing author order is retained.

| Artifact | Location |
| --- | --- |
| Compiled report | [main.pdf](main.pdf) |
| Main source | [main.tex](main.tex) |
| Model section | [taimoor_relational_section.tex](taimoor_relational_section.tex) |
| Queries and DML | [mason_query_dml_section.tex](mason_query_dml_section.tex) |
| Interface section | [shahmeer_ui_section.tex](shahmeer_ui_section.tex) |
| Complete third-page listing | [relations_constraints.tex](relations_constraints.tex) |
| Bibliography, including the AI tool citation | [taimoor_references.bib](taimoor_references.bib) |
| Architecture, exact calls | [system_architecture.pdf](../figures/system_architecture.pdf) |
| Enlarged UI excerpts | [ui_operations.pdf](../figures/ui_operations.pdf) |
| Full-resolution UI evidence | [Nine original captures](../figures/ui_screenshots/) |
| Submission ZIP | [4_Relational_Taimoor_Mason_Shahmeer.zip](../submission/4_Relational_Taimoor_Mason_Shahmeer.zip) |
| Correction and verification scope | [submission_review.md](../docs/submission_review.md) |

## Rebuild from the repository root

Install `requirements.txt` and a LaTeX distribution with `pdflatex`, BibTeX,
ACM `sigconf` packages/fonts (Libertine, Inconsolata and newtxmath) and `xurl`.
Standard Overleaf ACM environments provide these. Python dependencies alone do
not install LaTeX or its fonts. Poppler is optional for the PNG figure preview.

```sh
python -m pip install -r requirements.txt
python scripts/generate_report_figures.py
python scripts/build_m4_submission.py
```

The builder stages the exact standalone ZIP structure, compiles four passes,
checks the page count/third-page listing, repository links, undefined references,
overfull boxes, missing ACM fonts and ZIP integrity, and includes all nine screenshot supplements.
It publishes the report PDF and ZIP only after those checks pass. The original
screenshots are neither resized nor altered; supplementary PNGs are losslessly
compressed and checked for identical pixels. Inspect the resulting pages
visually as well, since automatic checks cannot establish legibility.

For manual compilation, run the four LaTeX/BibTeX commands in
[PACKAGE_README.md](PACKAGE_README.md) from this directory. The ZIP contains the
same main source and local figures, so it also compiles without the repository.

## Evaluation and attribution

AI assisted with the section drafts, implementation, figures, tests and final
report corrections. Taimoor's supplied design evaluation and Mason's reported
human reruns are distinguished from the assistant's verification. The report
cites the tool and project evaluation records.

The old `relations_constraints_preview.*` files are a historical standalone
layout preview, not the final report. The final listing retains the same
attributes and rules, with wrapping adjusted for the ACM fonts.
