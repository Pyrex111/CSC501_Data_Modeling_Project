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
