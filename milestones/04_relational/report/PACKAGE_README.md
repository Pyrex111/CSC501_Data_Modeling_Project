# Milestone 4 submission

The compiled report is `main.pdf`: exactly two report pages plus one page
listing all twelve relations and constraints. All team members are graduate
students; the existing author order is retained.

## Compile the self-contained source

Use a current LaTeX distribution or Overleaf with the ACM `sigconf` dependencies
(including Libertine, Inconsolata and newtxmath fonts), `xurl` and BibTeX.
From this directory:

```sh
pdflatex -interaction=nonstopmode -halt-on-error main.tex
bibtex main
pdflatex -interaction=nonstopmode -halt-on-error main.tex
pdflatex -interaction=nonstopmode -halt-on-error main.tex
```

The ACM class and bibliography style retain their own license notices. All
local sections, bibliography and required figure PDFs are included. The report
uses `figures/` here and `../figures/` when built in the project repository.

## Evidence and implementation

- `figures/system_architecture.pdf`: actual routes/helper/DAL/validator calls.
- `figures/ui_operations.pdf`: enlarged, explicitly cropped excerpts of the
  committed UI captures; intervening rows are omitted, not changed.
- `supplements/ui_screenshots/`: all nine full-resolution captures, including
  search, detail/provenance, portfolio dates, create, update, delete and rejected
  writes. Their pixels match the repository originals; PNG compression differs.
- All application/demo identities and observations are fictional. The synthetic
  PDFs illustrate provenance structure, not real-provider accuracy.

Code, SQL, reproducible database setup, synthetic source PDFs and per-member
AI-use/evaluation records are in the linked repository:
https://github.com/Pyrex111/CSC501_Data_Modeling_Project.

Run `python -m pip install -r requirements.txt`, then
`python quickstart.py --serve` from a checkout. Read the root README and
`milestones/04_relational/docs/submission_review.md` for verification scope.
The supplied judgments and assistant-executed checks are recorded separately.
