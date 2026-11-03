"""Run the analytical SQL queries against an ETF allocation database.

Usage:
    python -m dal.run_analysis_queries [path/to/database]
With no argument, an in-memory database is built from schema + seed so the
queries can be demonstrated from a clean checkout.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

from dal.seed_data import seed

SRC_ROOT = Path(__file__).resolve().parent
QUERIES_FILE = SRC_ROOT / "sql" / "analysis_queries.sql"
SCHEMA_FILE = SRC_ROOT / "sql" / "schema.sql"
PROJECT_ROOT = SRC_ROOT.parents[1]


def _strip_comments(sql: str) -> str:
    lines = []
    for line in sql.splitlines():
        idx = line.find("--")
        lines.append(line if idx == -1 else line[:idx])
    return "\n".join(lines)


def _split(sql: str) -> list[str]:
    return [s.strip() for s in _strip_comments(sql).split(";") if s.strip()]


def _build_in_memory() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:", isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_FILE.read_text())
    try:
        seed(conn, PROJECT_ROOT)
    except BaseException:
        conn.close()
        raise
    return conn


def _open_file(path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def main() -> None:
    if len(sys.argv) > 1:
        conn = _open_file(sys.argv[1])
    else:
        conn = _build_in_memory()

    for i, stmt in enumerate(_split(QUERIES_FILE.read_text()), start=1):
        rows = conn.execute(stmt).fetchall()
        columns = list(rows[0].keys()) if rows else []
        print(f"--- Q{i}: {len(rows)} row(s) ---")
        print(" | ".join(columns))
        for row in rows[:8]:
            print(" | ".join(str(v) for v in row))
        if len(rows) > 8:
            print(f"... {len(rows) - 8} more row(s)")
        print()
    conn.close()


if __name__ == "__main__":
    main()
