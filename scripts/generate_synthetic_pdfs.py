"""Generate the three readable synthetic retained-evidence PDFs.

The placeholder files in ``data/raw`` carry a ``.pdf`` name but contain plain
text. This script rebuilds them as genuine, openable PDFs using the values
stored in the demo database, so the retained source always matches the seed
data rather than a hand-written copy.

From the repository root:
    python scripts/generate_synthetic_pdfs.py
    python scripts/generate_synthetic_pdfs.py --database data/etf_allocations.sqlite3
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

ROOT = Path(__file__).resolve().parents[1]

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

SYNTHETIC_NOTICE = "Synthetic demonstration: all identities and observations are fictional."


def _fetch(connection: sqlite3.Connection) -> list[dict]:
    """Return one document descriptor per retained source file."""
    connection.row_factory = sqlite3.Row
    docs = []
    sources = connection.execute(
        "SELECT Id, CapturedFileRef, Url, RetrievedAt, PublishedAt, "
        "ETFProviderId FROM SourceDocument ORDER BY Id"
    ).fetchall()
    for source in sources:
        provider = connection.execute(
            "SELECT LegalName, RegistrationNumber, RegistrationJurisdiction "
            "FROM ETFProvider WHERE Id = ?",
            (source["ETFProviderId"],),
        ).fetchone()
        snapshots = connection.execute(
            "SELECT DISTINCT s.Id, s.AllocationAsOfDate, s.CoverageStatus, "
            "d.DimensionName FROM AllocationSnapshot s "
            "JOIN AllocationDimension d ON s.AllocationDimensionId = d.Id "
            "WHERE s.SourceDocumentId = ? ORDER BY d.DimensionName",
            (source["Id"],),
        ).fetchall()
        etf_ids = {
            row["ETFId"]
            for row in connection.execute(
                "SELECT DISTINCT ETFId FROM AllocationSnapshot "
                "WHERE SourceDocumentId = ?",
                (source["Id"],),
            ).fetchall()
        }
        etfs = []
        for etf_id in etf_ids:
            etf = connection.execute(
                "SELECT FundName FROM ETF WHERE Id = ?", (etf_id,)
            ).fetchone()
            identifiers = connection.execute(
                "SELECT IdentifierScheme, IdentifierValue, ExchangeContext "
                "FROM ETFIdentifier WHERE ETFId = ? ORDER BY IdentifierScheme",
                (etf_id,),
            ).fetchall()
            etfs.append({"fund": etf["FundName"], "identifiers": identifiers})
        tables = []
        for snapshot in snapshots:
            rows = connection.execute(
                "SELECT cat.Label, cat.Code, cat.ContextKey, en.WeightFraction "
                "FROM AllocationEntry en JOIN AllocationCategory cat "
                "ON en.AllocationCategoryId = cat.Id "
                "WHERE en.AllocationSnapshotId = ? ORDER BY cat.Label",
                (snapshot["Id"],),
            ).fetchall()
            scheme = connection.execute(
                "SELECT DISTINCT sc.SchemeAuthority, sc.SchemeName, sc.Version "
                "FROM AllocationEntry en JOIN AllocationCategory cat "
                "ON en.AllocationCategoryId = cat.Id "
                "LEFT JOIN ClassificationScheme sc ON cat.ClassificationSchemeId = sc.Id "
                "WHERE en.AllocationSnapshotId = ? AND sc.Id IS NOT NULL",
                (snapshot["Id"],),
            ).fetchall()
            tables.append(
                {
                    "dimension": snapshot["DimensionName"],
                    "as_of": snapshot["AllocationAsOfDate"],
                    "coverage": snapshot["CoverageStatus"],
                    "rows": rows,
                    "schemes": scheme,
                }
            )
        docs.append(
            {
                "path": source["CapturedFileRef"],
                "url": source["Url"],
                "retrieved": source["RetrievedAt"],
                "published": source["PublishedAt"],
                "provider": provider,
                "etfs": etfs,
                "tables": tables,
            }
        )
    return docs


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "DocTitle", parent=base["Title"], fontSize=16, spaceAfter=6
        ),
        "h2": ParagraphStyle(
            "H2", parent=base["Heading2"], fontSize=12, spaceBefore=10,
            spaceAfter=4
        ),
        "body": ParagraphStyle("Body", parent=base["BodyText"], fontSize=9.5),
        "notice": ParagraphStyle(
            "Notice", parent=base["BodyText"], fontSize=10.5,
            textColor=colors.HexColor("#7a1f1f"), leading=14
        ),
        "cell": ParagraphStyle("Cell", parent=base["BodyText"], fontSize=9),
    }


def _build_document(doc: dict, target: Path, styles: dict) -> None:
    story = []
    first_etf = doc["etfs"][0]
    story.append(Paragraph(first_etf["fund"], styles["title"]))
    story.append(Paragraph("Retained factsheet / product disclosure", styles["body"]))
    story.append(Spacer(1, 8))

    notice = Table(
        [[Paragraph(SYNTHETIC_NOTICE, styles["notice"])]],
        colWidths=[6.5 * inch],
    )
    notice.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#fbeaea")),
                ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#b03a3a")),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(notice)
    story.append(Spacer(1, 10))

    ticker = next(
        (i["IdentifierValue"] for i in first_etf["identifiers"]
         if i["IdentifierScheme"] == "Ticker"),
        "",
    )
    isin = next(
        (i["IdentifierValue"] for i in first_etf["identifiers"]
         if i["IdentifierScheme"] == "ISIN"),
        "",
    )
    exchange = next(
        (i["ExchangeContext"] for i in first_etf["identifiers"]
         if i["IdentifierScheme"] == "Ticker"),
        "",
    )
    meta = [
        ["Provider", doc["provider"]["LegalName"]],
        ["Provider registration",
         f"{doc['provider']['RegistrationNumber']} "
         f"({doc['provider']['RegistrationJurisdiction']})"],
        ["Source URL", doc["url"]],
        ["Ticker", f"{ticker} (exchange context {exchange})"],
        ["ISIN", isin],
        ["Retrieved at (UTC)", doc["retrieved"]],
        ["Published at", doc["published"] or "not recorded"],
    ]
    meta_table = Table(
        [[Paragraph(k, styles["cell"]), Paragraph(str(v), styles["cell"])]
         for k, v in meta],
        colWidths=[1.7 * inch, 4.8 * inch],
    )
    meta_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f2f4f7")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(meta_table)

    for table in doc["tables"]:
        story.append(Spacer(1, 10))
        heading = (
            f"{table['dimension']} allocations as of {table['as_of']} "
            f"({table['coverage']})"
        )
        story.append(Paragraph(heading, styles["h2"]))
        for scheme in table["schemes"]:
            version = scheme["Version"] or "version not recorded"
            story.append(
                Paragraph(
                    f"Classification: {scheme['SchemeAuthority']} - "
                    f"{scheme['SchemeName']} ({version})",
                    styles["body"],
                )
            )
        data = [["Category", "Code", "Weight"]]
        total = 0.0
        for row in table["rows"]:
            data.append(
                [
                    Paragraph(row["Label"], styles["cell"]),
                    row["Code"] or "-",
                    f"{row['WeightFraction']:.3f}",
                ]
            )
            total += row["WeightFraction"]
        data.append(["Total", "", f"{total:.3f}"])
        weight_table = Table(data, colWidths=[3.4 * inch, 1.5 * inch, 1.6 * inch])
        weight_table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8edf4")),
                    ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#f2f4f7")),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 5),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
                ]
            )
        )
        story.append(weight_table)

    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "All names, identifiers, dates and weights above are invented for "
            "demonstration. Source URLs use the reserved example.invalid domain "
            "and do not resolve to a real issuer.",
            styles["body"],
        )
    )

    target.parent.mkdir(parents=True, exist_ok=True)
    builder = SimpleDocTemplate(
        str(target),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.7 * inch,
        bottomMargin=0.7 * inch,
        title=first_etf["fund"],
    )
    builder.build(story)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--database",
        type=Path,
        default=ROOT / "data" / "etf_allocations.sqlite3",
    )
    parser.add_argument("--output-dir", type=Path, default=ROOT)
    args = parser.parse_args()
    if not args.database.exists():
        parser.error(f"Database not found: {args.database}; run quickstart.py first.")

    connection = sqlite3.connect(str(args.database))
    try:
        docs = _fetch(connection)
    finally:
        connection.close()

    styles = _styles()
    for doc in docs:
        target = args.output_dir / doc["path"]
        _build_document(doc, target, styles)
        print(f"Wrote {target}")
    print(f"Generated {len(docs)} synthetic PDF(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
