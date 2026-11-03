"""Database connection management (Mason).

Centralizes how the application opens SQLite connections:
  * foreign-key enforcement is enabled and verified on every connection;
  * rows are returned as sqlite3.Row (column-name access);
  * transactions are managed explicitly (isolation_level=None);
  * connections are always closed, and an error triggers a rollback.

The UI and business layers obtain connections only through this module and
never call sqlite3 directly.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
from typing import Union

# Canonical location of the application database.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "etf_allocations.sqlite3"


class ForeignKeyNotEnabledError(RuntimeError):
    """Raised when PRAGMA foreign_keys does not report 1."""


class Database:
    """Context manager wrapping one SQLite connection.

    Example
    -------
    >>> with Database(DEFAULT_DB_PATH) as conn:
    ...     rows = conn.execute("SELECT ... WHERE Id = ?", (id_,)).fetchall()
    """

    def __init__(self, db_path: Union[str, Path] = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None

    def __enter__(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(
            str(self.db_path),
            detect_types=sqlite3.PARSE_DECLTYPES,
            isolation_level=None,  # explicit BEGIN/COMMIT/ROLLBACK
        )
        self._connection.row_factory = sqlite3.Row
        self._enable_foreign_keys(self._connection)
        return self._connection

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._connection is None:
            return
        if exc_type is not None and self._connection.in_transaction:
            self._connection.rollback()
        self._connection.close()
        self._connection = None

    @staticmethod
    def _enable_foreign_keys(conn: sqlite3.Connection) -> None:
        conn.execute("PRAGMA foreign_keys = ON")
        status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        if status != 1:
            raise ForeignKeyNotEnabledError(
                "Foreign-key enforcement could not be enabled "
                f"(PRAGMA foreign_keys = {status})."
            )

    @staticmethod
    def verify_foreign_keys(conn: sqlite3.Connection) -> int:
        """Return the current foreign-key setting (used as evidence)."""
        return conn.execute("PRAGMA foreign_keys").fetchone()[0]


def connect(db_path: Union[str, Path] = DEFAULT_DB_PATH) -> Database:
    """Factory for readability in the application layer."""
    return Database(db_path)
