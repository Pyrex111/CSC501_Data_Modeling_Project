# Milestone 5 report and submission

`main.tex` combines the ontology, graph/SPARQL backend and graph-backed interface
contributions, the architecture diagram, UI evidence, AI attribution and
references. The compiled `main.pdf` is exactly three ACM `sigconf` double-column
pages. All members are graduate students, so the existing author order is
retained: Taimoor Shahzad, M. Shahmeer Ather Kakwan, Mason Li.

| Artifact | Location |
| --- | --- |
| Compiled report | [main.pdf](main.pdf) |
| Main source | [main.tex](main.tex) |
| Ontology, FIBO boundary and validator split | [mason_ontology_section.tex](mason_ontology_section.tex) |
| Graph population, SPARQL parity and reproducibility | [taimoor_semantic_section.tex](taimoor_semantic_section.tex) |
| Graph-backed Flask interface | [shahmeer_ui_semantic_section.tex](shahmeer_ui_semantic_section.tex) |
| Ontology alignment and rule-split tables | [tables/](tables/) |
| Bibliography, including the AI tool citation | [references.bib](references.bib) |
| M5 layer diagram | [system_architecture_m5.pdf](../figures/system_architecture_m5.pdf) |
| Wide call diagram used in the report | [system_architecture_m5_wide.pdf](../figures/system_architecture_m5_wide.pdf) |
| Full-resolution UI captures | [../docs/screenshots/](../docs/screenshots/) |
| Self-contained submission ZIP | [../submission/5_Semantic_Taimoor_Mason_Shahmeer.zip](../submission/5_Semantic_Taimoor_Mason_Shahmeer.zip) |

## Rebuild from this directory

Install a LaTeX distribution with `pdflatex`, BibTeX, the ACM `sigconf`
dependencies (Libertine, Inconsolata and newtxmath fonts) and `xurl`. Standard
Overleaf ACM environments provide these.

```sh
pdflatex -interaction=nonstopmode main.tex
bibtex main
pdflatex -interaction=nonstopmode main.tex
pdflatex -interaction=nonstopmode main.tex
```

The ACM class and bibliography style retain their own license notices. The 189-test
suite, ontology file, graph validator, backend hook, SPARQL queries and seed data
live at the repository root and under `src/`, `tests/` and
`milestones/05_semantic/`. All demonstration records are synthetic; no real
customer, fund or source document is used.

## Final submission rebuild

After compiling the report, run `python scripts/package_m5_submission.py` from
the repository root. It requires exactly three PDF pages and eleven screenshots,
packages the sources and executable query, and adds a SHA-256 manifest. The wide
diagram shows routes calling business helpers and graph access separately.
Final assistant-executed verification is recorded in
[final_revision_verification.md](../docs/final_revision_verification.md).

The expanded final revision includes a six-query coverage table, query
interpretation and concrete CRUD evaluation. Inspect all three rendered pages
after any rebuild: exactly three PDF pages alone does not establish that the
space is used adequately. The final page has substantive content in both columns
to the normal bottom text area.
