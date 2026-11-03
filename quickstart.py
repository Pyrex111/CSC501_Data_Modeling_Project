#!/usr/bin/env python3
"""Quickstart: create or reuse a demo database and optionally
run the analytical queries or launch the Flask application.

From a clean checkout:
    python quickstart.py             # build + seed + row counts
    python quickstart.py --queries   # also run the six analytical queries
    python quickstart.py --serve     # also launch the Flask UI when available
    python quickstart.py --reset     # explicitly replace the database with demo data
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dal.database import DEFAULT_DB_PATH  # noqa: E402
from dal.seed_data import seed  # noqa: E402
from dal.schema_validation import validate_database  # noqa: E402

SCHEMA_FILE = PROJECT_ROOT / "src" / "dal" / "sql" / "schema.sql"


def build(db_path: Path, *, reset: bool = False) -> None:
    """Build and validate before publishing; replacement requires explicit reset."""
    if db_path.exists() and not reset:
        raise FileExistsError(f"Database already exists: {db_path}; use --reset to replace it.")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='etf-build-', dir=db_path.parent) as directory:
        candidate = Path(directory) / 'demo.sqlite3'
        connection = sqlite3.connect(str(candidate), isolation_level=None)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            connection.executescript(SCHEMA_FILE.read_text())
            if connection.execute("PRAGMA foreign_keys").fetchone()[0] != 1:
                raise RuntimeError("Foreign-key enforcement could not be enabled.")
            seed(connection, PROJECT_ROOT)
        finally:
            connection.close()
        if reset:
            os.replace(candidate, db_path)
        else:
            # Atomic creation also refuses a file created since the check above.
            os.link(candidate, db_path)


def table_counts(db_path: Path) -> dict[str, int]:
    connection = sqlite3.connect(str(db_path))
    try:
        names = [
            r[0]
            for r in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name != 'sqlite_sequence' ORDER BY name"
            )
        ]
        return {
            n: connection.execute(f"SELECT COUNT(*) FROM {n}").fetchone()[0]
            for n in names
        }
    finally:
        connection.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="ETF allocations quickstart")
    parser.add_argument("--serve", action="store_true")
    parser.add_argument("--queries", action="store_true")
    parser.add_argument("--reset", action="store_true", help="replace existing data with the demo seed")
    args = parser.parse_args()

    if args.reset or not DEFAULT_DB_PATH.exists():
        print("Building database:", DEFAULT_DB_PATH)
        build(DEFAULT_DB_PATH, reset=args.reset)
        print("Seed data loaded.\n")
    else:
        print("Reusing database:", DEFAULT_DB_PATH)
        connection = sqlite3.connect(str(DEFAULT_DB_PATH))
        try:
            connection.execute("PRAGMA foreign_keys = ON")
            validate_database(connection, capture_root=PROJECT_ROOT)
        finally:
            connection.close()

    print("Row counts:")
    for name, count in table_counts(DEFAULT_DB_PATH).items():
        print(f"  {name:22s} {count}")

    if args.queries:
        print("\nRunning analytical queries...\n")
        from dal import run_analysis_queries
        sys.argv = ["run_analysis_queries.py", str(DEFAULT_DB_PATH)]
        run_analysis_queries.main()

    if args.serve:
        app_path = PROJECT_ROOT / "src" / "ui" / "app.py"
        if not app_path.exists():
            print("\nFlask UI (src/ui/app.py) is not available yet; database is ready.")
            return 0
        print("\nStarting Flask application...")
        import subprocess
        subprocess.run([sys.executable, str(app_path)], check=True)
    else:
        print("\nQuickstart complete. Re-run with --serve to start the UI.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
