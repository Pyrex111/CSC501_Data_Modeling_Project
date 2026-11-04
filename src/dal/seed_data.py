"""Reproducible seed loader for the fully synthetic demonstration dataset.

Every record is fictional: customers, providers, source identities, captured
files, classification examples, labels and all weights. Source URLs use the
reserved ``example.invalid`` domain and are not real addresses.

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

# Fictional UTC capture timestamps (27 characters, six fractional digits).
RET_SYA = "2026-09-23T09:15:00.000000Z"
RET_SYB = "2026-09-23T09:20:00.000000Z"
RET_SYC = "2026-09-23T09:25:00.000000Z"

# Fictional source URLs on the reserved example.invalid domain.
URL_SYA = "https://provider.example.invalid/funds/sya/facts"
URL_SYB = "https://provider.example.invalid/funds/syb/facts"
URL_SYC = "https://manager.example.invalid/funds/syc/facts"

# One basis note reused by every snapshot.
BASIS = "Fully synthetic demonstration: all identities and weights are fictional."


def seed(connection: sqlite3.Connection, capture_root: Path) -> None:
    """Insert the full fictional dataset inside one validated transaction."""
    with validated_transaction(connection, capture_root=capture_root):
        # 1. Customers -----------------------------------------------------
        connection.executemany(
            "INSERT INTO Customer VALUES (?, ?, ?, ?, ?)",
            [
                (1, "1001", "Alice", "Chen", "alice.chen@example.invalid"),
                (2, "1002", "Brian", "Li", None),
            ],
        )

        # 2. Providers (fictional registration details) -------------------
        connection.executemany(
            "INSERT INTO ETFProvider VALUES (?, ?, ?, ?, ?)",
            [
                (1, "Example Fund Management Ltd.",
                 "SYN-REG-001", "SYNTHETIC",
                 "https://provider.example.invalid"),
                (2, "Demonstration Asset Managers Inc.",
                 "SYN-REG-002", "SYNTHETIC",
                 "https://manager.example.invalid"),
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
                (1, "Example Standards Body", "Demo Sector Scheme", "v1", None),
                (2, "Example Fund Management Ltd.",
                 "Demo Regional Scheme", None, None),
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
                (1, 1, "Example Large-Cap Equity ETF", "CA", "CAD", None),
                (2, 1, "Example Broad Market Equity ETF", "CA", "CAD", None),
                (3, 2, "Demonstration Domestic Composite ETF",
                 "CA", "CAD", None),
            ],
        )

        # 7. Identifiers (fictional ISIN + Ticker per ETF) ----------------
        connection.executemany(
            "INSERT INTO ETFIdentifier VALUES (?, ?, ?, ?, ?)",
            [
                (1, 1, "ISIN", "ZZ0000000001", None),
                (2, 1, "Ticker", "SYA", "XDEM"),
                (3, 2, "ISIN", "ZZ0000000002", None),
                (4, 2, "Ticker", "SYB", "XDEM"),
                (5, 3, "ISIN", "ZZ0000000003", None),
                (6, 3, "Ticker", "SYC", "XDEM"),
            ],
        )

        # 8. Holdings (fictional portfolio weights) ------------------------
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
                (1, 1, URL_SYA, RET_SYA, None,
                 "data/raw/example_sya_facts_20260716.pdf",
                 "Example SYA ETF Facts"),
                (2, 1, URL_SYB, RET_SYB, None,
                 "data/raw/example_syb_facts_20260716.pdf",
                 "Example SYB ETF Facts"),
                (3, 2, URL_SYC, RET_SYC, None,
                 "data/raw/demo_syc_product_20260801.pdf",
                 "Demo SYC Product Page"),
            ],
        )

        # 10. Categories ---------------------------------------------------
        sector_ctx = scheme_context("Example Standards Body",
                                    "Demo Sector Scheme", "v1")
        sya_geo = disclosure_context(URL_SYA, RET_SYA,
                                     "geography-table", "Geography")
        syb_geo = disclosure_context(URL_SYB, RET_SYB,
                                     "geography-table", "Geography")
        syc_geo = disclosure_context(URL_SYC, RET_SYC,
                                     "geography-table", "Geography")

        # Sector categories under the known fictional edition (dimension 1).
        connection.executemany(
            "INSERT INTO AllocationCategory VALUES (?, ?, ?, ?, ?, ?)",
            [
                (1, 1, 1, "Information Technology", "DEMO-45", sector_ctx),
                (2, 1, 1, "Financials", "DEMO-40", sector_ctx),
                (3, 1, 1, "Consumer Discretionary", "DEMO-25", sector_ctx),
                (4, 1, 1, "Energy", "DEMO-10", sector_ctx),
                (5, 1, 1, "Other Sectors", None, sector_ctx),
            ],
        )
        # Geography categories, disclosure-local contexts (dimension 2).
        connection.executemany(
            "INSERT INTO AllocationCategory VALUES (?, ?, ?, ?, ?, ?)",
            [
                (6, 2, None, "United States", None, sya_geo),
                (7, 2, None, "Canada", None, sya_geo),
                (8, 2, None, "Other / Multi-region", None, sya_geo),
                (9, 2, None, "United States", None, syb_geo),
                (10, 2, None, "Other / Multi-region", None, syb_geo),
                (11, 2, None, "Canada", None, syc_geo),
                (12, 2, None, "United States", None, syc_geo),
                (13, 2, None, "Other / Multi-region", None, syc_geo),
            ],
        )

        # 11. Snapshots ----------------------------------------------------
        connection.executemany(
            "INSERT INTO AllocationSnapshot VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            [
                (1, 1, 2, 1, "2026-05-31", BASIS, "Complete", "geography-table"),
                (2, 1, 1, 1, "2026-05-31", BASIS, "Complete", "sector-table"),
                (3, 2, 2, 2, "2026-05-31", BASIS, "Complete", "geography-table"),
                (4, 3, 2, 3, "2026-06-30", BASIS, "Complete", "geography-table"),
                (5, 3, 1, 3, "2026-06-30", BASIS, "Complete", "sector-table"),
            ],
        )

        # 12. Entries (17; every Complete snapshot sums to 1.0) -----------
        connection.executemany(
            "INSERT INTO AllocationEntry VALUES (?, ?, ?, ?)",
            [
                # SYA geography
                (1, 1, 6, 0.985), (2, 1, 7, 0.010), (3, 1, 8, 0.005),
                # SYA sector (fictional scheme)
                (4, 2, 1, 0.310), (5, 2, 2, 0.130), (6, 2, 3, 0.105),
                (7, 2, 4, 0.040), (8, 2, 5, 0.415),
                # SYB geography
                (9, 3, 9, 0.995), (10, 3, 10, 0.005),
                # SYC geography
                (11, 4, 11, 0.975), (12, 4, 12, 0.020), (13, 4, 13, 0.005),
                # SYC sector (fictional scheme)
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
                        default=ROOT / "data/etf_allocations.sqlite3")
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
