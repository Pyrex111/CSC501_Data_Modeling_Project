"""Reproducible seed loader for the demonstration dataset.

All writes are parameterized (execute/executemany) and run inside Taimoor's
``validated_transaction``, so the whole dataset is rejected and rolled back if
it violates any model rule. ContextKey tokens are produced by the documented
helpers rather than hand-written.

Run from the repository root:
    python -m dal.seed_data --database data/etf_allocations.sqlite3
"""
from __future__ import annotations

import argparse
from pathlib import Path
import sqlite3
import sys

from dal.schema_validation import (
    disclosure_context,
    scheme_context,
    validated_transaction,
)

ROOT = Path(__file__).resolve().parents[2]

# Canonical UTC capture timestamps (27 characters, six fractional digits).
RET_VFV = "2026-09-23T09:15:00.000000Z"
RET_VUN = "2026-09-23T09:20:00.000000Z"
RET_XIC = "2026-09-23T09:25:00.000000Z"

URL_VFV = ("https://www.vanguard.ca/en/product/etf/equity/9563/"
           "vanguard-sp-500-index-etf")
URL_VUN = ("https://www.vanguard.ca/en/product/etf/equity/9511/"
           "vanguard-us-total-market-index-etf")
URL_XIC = ("https://www.blackrock.com/ca/investors/en/products/239837/"
           "ishares-sptsx-capped-composite-index-etf")


def seed(connection: sqlite3.Connection, capture_root: Path) -> None:
    """Insert the full demonstration dataset inside one validated transaction."""
    with validated_transaction(connection, capture_root=capture_root):
        # 1. Customers -----------------------------------------------------
        connection.executemany(
            "INSERT INTO Customer VALUES (?, ?, ?, ?, ?)",
            [
                (1, "1001", "Alice", "Chen", "alice.chen@example.invalid"),
                (2, "1002", "Brian", "Li", None),
            ],
        )

        # 2. Providers (registration numbers are labelled placeholders) ----
        connection.executemany(
            "INSERT INTO ETFProvider VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Vanguard Investments Canada Inc.",
                 "REG-PLACEHOLDER-VAN", "CA-FEDERAL",
                 "https://www.vanguard.ca"),
                (2, "BlackRock Asset Management Canada Limited",
                 "REG-PLACEHOLDER-BLK", "CA-FEDERAL",
                 "https://www.blackrock.com/ca"),
            ],
        )

        # 3. Dimensions ----------------------------------------------------
        connection.executemany(
            "INSERT INTO AllocationDimension VALUES (?, ?)",
            [(1, "Sector"), (2, "Geography")],
        )

        # 4. Classification schemes (one known version, one unknown) -------
        connection.executemany(
            "INSERT INTO ClassificationScheme VALUES (?, ?, ?, ?, ?)",
            [
                (1, "S&P Dow Jones Indices", "GICS", "2025", None),
                (2, "Vanguard Investments Canada",
                 "Regional Classification", None, None),
            ],
        )

        # 5. Portfolios ----------------------------------------------------
        connection.executemany(
            "INSERT INTO Portfolio VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, "P-ALICE-01", "Growth Portfolio", "CAD"),
                (2, 2, "P-BRIAN-01", "Balanced Portfolio", "CAD"),
            ],
        )

        # 6. ETFs ----------------------------------------------------------
        connection.executemany(
            "INSERT INTO ETF VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 1, "Vanguard S&P 500 Index ETF", "CA", "CAD", None),
                (2, 1, "Vanguard U.S. Total Market Index ETF", "CA", "CAD", None),
                (3, 2, "iShares Core S&P/TSX Capped Composite Index ETF",
                 "CA", "CAD", None),
            ],
        )

        # 7. Identifiers (ISIN + Ticker per ETF) ---------------------------
        connection.executemany(
            "INSERT INTO ETFIdentifier VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, "ISIN", "CA9229081082", None),
                (2, 1, "Ticker", "VFV", "XTSX"),
                (3, 2, "ISIN", "CA9229071034", None),
                (4, 2, "Ticker", "VUN", "XTSX"),
                (5, 3, "ISIN", "CA46430J1005", None),
                (6, 3, "Ticker", "XIC", "XTSX"),
            ],
        )

        # 8. Holdings (synthetic portfolio weights) ------------------------
        connection.executemany(
            "INSERT INTO Holding VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, 1, 0.60, "2026-08-01"),
                (2, 1, 3, 0.40, "2026-08-01"),
                (3, 2, 1, 0.30, "2026-08-01"),
                (4, 2, 2, 0.20, "2026-08-01"),
                (5, 2, 3, 0.50, "2026-08-01"),
            ],
        )

        # 9. Source documents (PublishedAt unknown -> NULL) ---------------
        connection.executemany(
            "INSERT INTO SourceDocument VALUES (?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 1, URL_VFV, RET_VFV, None,
                 "data/raw/vanguard_vfv_etf_facts_20260716.pdf",
                 "Vanguard VFV ETF Facts"),
                (2, 1, URL_VUN, RET_VUN, None,
                 "data/raw/vanguard_vun_etf_facts_20260716.pdf",
                 "Vanguard VUN ETF Facts"),
                (3, 2, URL_XIC, RET_XIC, None,
                 "data/raw/blackrock_xic_product_20260801.pdf",
                 "BlackRock iShares XIC Product Page"),
            ],
        )

        # 10. Categories ---------------------------------------------------
        gics_ctx = scheme_context("S&P Dow Jones Indices", "GICS", "2025")
        vfv_geo = disclosure_context(URL_VFV, RET_VFV, "geography-table", "Geography")
        vun_geo = disclosure_context(URL_VUN, RET_VUN, "geography-table", "Geography")
        xic_geo = disclosure_context(URL_XIC, RET_XIC, "geography-table", "Geography")

        # Sector categories under the known GICS edition (dimension 1).
        connection.executemany(
            "INSERT INTO AllocationCategory VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 1, 1, "Information Technology", "GICS25-45", gics_ctx),
                (2, 1, 1, "Financials", "GICS25-40", gics_ctx),
                (3, 1, 1, "Consumer Discretionary", "GICS25-25", gics_ctx),
                (4, 1, 1, "Energy", "GICS25-10", gics_ctx),
                (5, 1, 1, "Other Sectors", None, gics_ctx),
            ],
        )
        # Geography categories, disclosure-local contexts (dimension 2).
        connection.executemany(
            "INSERT INTO AllocationCategory VALUES (?, ?, ?, ?, ?, ?)",
            [
                (6, 2, None, "United States", None, vfv_geo),
                (7, 2, None, "Canada", None, vfv_geo),
                (8, 2, None, "Other / Multi-region", None, vfv_geo),
                (9, 2, None, "United States", None, vun_geo),
                (10, 2, None, "Other / Multi-region", None, vun_geo),
                (11, 2, None, "Canada", None, xic_geo),
                (12, 2, None, "United States", None, xic_geo),
                (13, 2, None, "Other / Multi-region", None, xic_geo),
            ],
        )

        # 11. Snapshots ----------------------------------------------------
        basis = ("Synthetic illustrative weights; identifying facts are real "
                 "and sourced.")
        connection.executemany(
            "INSERT INTO AllocationSnapshot VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 1, 2, 1, "2026-05-31", basis, "Complete", "geography-table"),
                (2, 1, 1, 1, "2026-05-31", basis, "Complete", "sector-table"),
                (3, 2, 2, 2, "2026-05-31", basis, "Complete", "geography-table"),
                (4, 3, 2, 3, "2026-06-30", basis, "Complete", "geography-table"),
                (5, 3, 1, 3, "2026-06-30", basis, "Complete", "sector-table"),
            ],
        )

        # 12. Entries (17; every Complete snapshot sums to 1.0) -----------
        connection.executemany(
            "INSERT INTO AllocationEntry VALUES (?, ?, ?, ?)",
            [
                # VFV geography
                (1, 1, 6, 0.985), (2, 1, 7, 0.010), (3, 1, 8, 0.005),
                # VFV sector (GICS)
                (4, 2, 1, 0.310), (5, 2, 2, 0.130), (6, 2, 3, 0.105),
                (7, 2, 4, 0.040), (8, 2, 5, 0.415),
                # VUN geography
                (9, 3, 9, 0.995), (10, 3, 10, 0.005),
                # XIC geography
                (11, 4, 11, 0.975), (12, 4, 12, 0.020), (13, 4, 13, 0.005),
                # XIC sector (GICS)
                (14, 5, 2, 0.320), (15, 5, 4, 0.175), (16, 5, 1, 0.095),
                (17, 5, 5, 0.410),
            ],
        )


def open_connection(db_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(db_path), isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
        raise RuntimeError("Foreign-key enforcement could not be enabled.")
    return connection


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path,
                        default=ROOT / "data" / "etf_allocations.sqlite3")
    args = parser.parse_args()
    db_path = args.database
    if not db_path.exists():
        parser.error(
            f"Database not found: {db_path}. Create the schema first "
            "(python scripts/create_schema.py --database ...)."
        )

    connection = open_connection(db_path)
    try:
        seed(connection, ROOT)
    finally:
        connection.close()
    print(f"Seeded demonstration dataset into {db_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
