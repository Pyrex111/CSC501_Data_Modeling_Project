"""Compile and package the M4 report; publish only after structural checks pass.

Requires requirements.txt and a LaTeX distribution with pdflatex, BibTeX and
ACM sigconf dependencies. The staged tree is exactly the self-contained ZIP.
"""
from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
import shutil
import subprocess
import tempfile
from zipfile import ZipFile, ZIP_DEFLATED

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
MILESTONE = ROOT / "milestones/04_relational"
REPORT = MILESTONE / "report"
STEM = "4_Relational_Taimoor_Mason_Shahmeer"
SOURCES = (
    "main.tex", "taimoor_relational_section.tex", "mason_query_dml_section.tex",
    "shahmeer_ui_section.tex", "relations_constraints.tex",
    "taimoor_references.bib", "acmart.cls", "ACM-Reference-Format.bst",
)
RELATIONS = (
    "Customer", "Portfolio", "Holding", "ETFProvider", "ETF", "ETFIdentifier",
    "SourceDocument", "AllocationDimension", "ClassificationScheme",
    "AllocationCategory", "AllocationSnapshot", "AllocationEntry",
)


def run(command, directory):
    result = subprocess.run(command, cwd=directory, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Build failed: " + " ".join(command) + "\n" +
                           result.stdout[-6000:] + result.stderr[-2000:])
    return result.stdout


def check_report(path):
    reader = PdfReader(path)
    if len(reader.pages) != 3:
        raise ValueError(f"Expected 2 report pages + 1 relation page; got {len(reader.pages)}.")
    listing = reader.pages[2].extract_text()
    if "Relations and constraints" not in listing:
        raise ValueError("Relation listing must begin on page 3.")
    missing = [name for name in RELATIONS if name not in listing]
    if missing:
        raise ValueError("Missing relations on page 3: " + ", ".join(missing))
    if any("Relations and constraints" in p.extract_text() for p in reader.pages[:2]):
        raise ValueError("The relation listing starts before page 3.")
    first = reader.pages[0]
    repo_links = []
    for ref in first.get("/Annots", []):
        action = ref.get_object().get("/A", {})
        if action.get("/URI") == "https://github.com/Pyrex111/CSC501_Data_Modeling_Project":
            repo_links.append(action)
    if len(repo_links) < 2:
        raise ValueError("Expected repository links in both abstract and title footnote.")
    return reader


def lossless_screenshot(source, destination):
    """Compress the original pixels, without resizing or changing their mode."""
    with Image.open(source) as original:
        before = original.tobytes()
        original.save(destination, optimize=True)
        with Image.open(destination) as saved:
            if saved.mode != original.mode or saved.size != original.size or saved.tobytes() != before:
                raise ValueError(f"Screenshot pixels changed: {source}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=MILESTONE / "submission")
    args = parser.parse_args()
    for tool in ("pdflatex", "bibtex"):
        if not shutil.which(tool):
            parser.error(f"Missing {tool}; see the report README for LaTeX requirements.")
    with tempfile.TemporaryDirectory(prefix="m4-report-") as temporary:
        stage = Path(temporary) / STEM
        stage.mkdir()
        for filename in SOURCES:
            shutil.copy2(REPORT / filename, stage / filename)
        figures = stage / "figures"
        figures.mkdir()
        for filename in ("system_architecture.pdf", "ui_operations.pdf"):
            shutil.copy2(MILESTONE / "figures" / filename, figures / filename)
        run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], stage)
        run(["bibtex", "main"], stage)
        run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], stage)
        final_log = run(["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "main.tex"], stage)
        check_report(stage / "main.pdf")
        if "You do not have the" in final_log:
            raise ValueError("Install the ACM font packages listed in the report README; fallback fonts are not accepted.")
        if "Overfull \\hbox" in final_log or "Overfull \\vbox" in final_log:
            raise ValueError("Report contains an overfull box; inspect the LaTeX layout before publishing.")
        if "undefined references" in final_log or "Citation `" in final_log:
            raise ValueError("Unresolved references or citations in final LaTeX pass.")
        supplements = stage / "supplements/ui_screenshots"
        supplements.mkdir(parents=True)
        captures = sorted((MILESTONE / "figures/ui_screenshots").glob("*.png"))
        if len(captures) != 9:
            raise ValueError(f"Expected nine original UI captures; found {len(captures)}.")
        for source in captures:
            lossless_screenshot(source, supplements / source.name)
        shutil.copy2(REPORT / "PACKAGE_README.md", stage / "README.md")
        # Build files are useful locally but not source deliverables.
        for extension in ("aux", "log", "out", "bbl", "blg"):
            (stage / f"main.{extension}").unlink(missing_ok=True)
        zip_path = Path(temporary) / f"{STEM}.zip"
        with ZipFile(zip_path, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(stage.parent))
        with ZipFile(zip_path) as archive:
            if archive.testzip() is not None:
                raise ValueError("ZIP integrity check failed.")
            check_report(BytesIO(archive.read(f"{STEM}/main.pdf")))
        args.output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / "main.pdf", REPORT / "main.pdf")
        shutil.copy2(zip_path, args.output_dir / zip_path.name)
        print("Validated: 3 pages, all 12 relations on page 3, live repository links,")
        print("no overfull boxes or unresolved references, 9 pixel-identical screenshot supplements.")
        print("PDF:", REPORT / "main.pdf")
        print("ZIP:", args.output_dir / zip_path.name)


if __name__ == "__main__":
    main()
