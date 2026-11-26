"""Package the compiled M5 report and exact sources after the final rebuild.

Requires pypdf from requirements.txt. Run from the repository root after compiling
milestones/05_semantic/report/main.tex. Refuses a report other than three pages.
"""

import hashlib
import json
from pathlib import Path
import tempfile
from zipfile import ZIP_DEFLATED, ZipFile

from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
M5 = ROOT / "milestones/05_semantic"
REPORT = M5 / "report"
NAME = "5_Semantic_Taimoor_Mason_Shahmeer"

README = """# Milestone 5 submission

main.pdf is the compiled three-page ACM sigconf report. All demonstration data
are synthetic. The package includes the exact report sources, executable SPARQL
example, architecture PDF/PNG/DOT files and eleven original UI screenshots.
MANIFEST.json records SHA-256 checksums of every other packaged file.

## Compile

Use a LaTeX distribution with the ACM sigconf dependencies (Libertine,
Inconsolata and newtxmath), xurl, pdflatex and BibTeX. From this directory:

    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    bibtex main
    pdflatex -interaction=nonstopmode -halt-on-error main.tex
    pdflatex -interaction=nonstopmode -halt-on-error main.tex

Check that the rebuilt PDF remains exactly three pages. The figure is in figures/
and the displayed query is read from examples/taimoor_snapshot_totals.sparql.
ACM class/style and third-party software retain their original license notices.

## Application and verification

https://github.com/Pyrex111/CSC501_Data_Modeling_Project

From a checkout, install requirements-semantic.txt and run:

    python quickstart_semantic.py --compare
    python quickstart_semantic.py --serve
    python -m unittest discover -s tests -q

Stop the server before opening the same persistent store in another process.
The report credits both ChatGPT/Codex and Claude. Automated checks are
assistant-executed; student design review is recorded separately.
"""


def main():
    pdf = REPORT / "main.pdf"
    reader = PdfReader(pdf)
    if len(reader.pages) != 3:
        raise ValueError("The final report must contain exactly three pages")
    text = " ".join((p.extract_text() or "") for p in reader.pages)
    for marker in ("SELECT", "Claude", "Codex", "189"):
        if marker not in text:
            raise ValueError(f"Expected report content is missing: {marker}")

    entries = {"README.md": README.encode(), "main.pdf": pdf.read_bytes()}
    for path in sorted(REPORT.rglob("*")):
        if path.is_file() and path.suffix in {".tex", ".bib", ".cls", ".bst", ".sparql"}:
            entries[path.relative_to(REPORT).as_posix()] = path.read_bytes()
    for path in sorted((M5 / "figures").glob("system_architecture_m5*")):
        if path.suffix in {".pdf", ".png", ".dot"}:
            entries["figures/" + path.name] = path.read_bytes()
    screenshots = sorted((M5 / "docs/screenshots").glob("*.png"))
    if len(screenshots) != 11:
        raise ValueError("Expected all eleven original UI screenshots")
    for path in screenshots:
        entries["supplements/ui_screenshots/" + path.name] = path.read_bytes()
    if "examples/taimoor_snapshot_totals.sparql" not in entries:
        raise ValueError("The executable report example must be packaged")
    manifest = {
        "report_pages": 3,
        "screenshots": 11,
        "sha256": {name: hashlib.sha256(data).hexdigest() for name, data in entries.items()},
    }
    entries["MANIFEST.json"] = (json.dumps(manifest, indent=2) + "\n").encode()

    destination = M5 / "submission" / (NAME + ".zip")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination.parent) as temporary:
        candidate = Path(temporary) / destination.name
        with ZipFile(candidate, "w", ZIP_DEFLATED, compresslevel=9) as archive:
            for name, data in sorted(entries.items()):
                archive.writestr(NAME + "/" + name, data)
        with ZipFile(candidate) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity check failed")
            for name, data in entries.items():
                if archive.read(NAME + "/" + name) != data:
                    raise ValueError("Packaged content mismatch: " + name)
        candidate.replace(destination)
    print(f"Created {destination}: {len(entries)} files, 3 pages, 11 screenshots")


if __name__ == "__main__":
    main()
