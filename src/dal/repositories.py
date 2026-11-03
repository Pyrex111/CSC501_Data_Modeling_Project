"""Parameterized data-access repository (Mason).

All user values are bound through placeholders (no SQL string building), so
the interface cannot be SQL-injected. Reads use plain SELECTs; every write
runs inside Taimoor's ``validated_transaction`` and is fully rolled back if
the resulting database state violates the model rules.

Rows are returned as plain dicts so the Flask layer can serialize to JSON.
"""
from __future__ import annotations

from typing import Any
import sqlite3

from dal.schema_validation import (
    ModelIntegrityError,
    validated_transaction,
)

# ---------------------------------------------------------------------------
# Domain errors surfaced to the UI
# ---------------------------------------------------------------------------
class RepositoryError(Exception):
    """Base error for data-access rule violations."""


class ValidationError(RepositoryError):
    """A required field or value range is invalid."""


class NotFoundError(RepositoryError):
    """The requested record does not exist."""


class BusinessRuleError(RepositoryError):
    """An operation would leave the model in an invalid state."""


def _validate_weight(weight: Any) -> float:
    if weight is None:
        raise ValidationError("Weight is required.")
    try:
        weight = float(weight)
    except (TypeError, ValueError):
        raise ValidationError("Weight must be a number.")
    if not 0.0 <= weight <= 1.0:
        raise ValidationError("Weight must be between 0 and 1 (fraction).")
    return weight


# ===========================================================================
# READS
# ===========================================================================
def search_disclosures(
    conn: sqlite3.Connection,
    ticker: str | None = None,
    dimension_name: str | None = None,
    as_of_date: str | None = None,
) -> list[dict]:
    """Search snapshots by ticker, dimension and/or observation date.

    The ticker is resolved through ETFIdentifier (ETF has no fund-code column).
    """
    sql = """
        SELECT s.Id AS SnapshotId,
               e.Id AS ETFId,
               (SELECT i.IdentifierValue FROM ETFIdentifier i
                  WHERE i.ETFId = e.Id AND i.IdentifierScheme = 'Ticker'
                  LIMIT 1) AS Ticker,
               e.FundName,
               d.DimensionName,
               s.AllocationAsOfDate,
               s.CoverageStatus,
               p.LegalName AS ProviderName,
               doc.Url
        FROM AllocationSnapshot s
        JOIN ETF                 e   ON e.Id = s.ETFId
        JOIN AllocationDimension d   ON d.Id = s.AllocationDimensionId
        JOIN SourceDocument      doc ON doc.Id = s.SourceDocumentId
        JOIN ETFProvider         p   ON p.Id = e.ETFProviderId
        WHERE 1 = 1
    """
    params: list[Any] = []
    if ticker:
        sql += """
            AND EXISTS (
                SELECT 1 FROM ETFIdentifier i
                WHERE i.ETFId = e.Id
                  AND i.IdentifierScheme = 'Ticker'
                  AND i.IdentifierValue = ?)
        """
        params.append(ticker)
    if dimension_name:
        sql += " AND d.DimensionName = ?"
        params.append(dimension_name)
    if as_of_date:
        sql += " AND s.AllocationAsOfDate = ?"
        params.append(as_of_date)
    sql += " ORDER BY s.AllocationAsOfDate, Ticker"
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def get_allocation_entries(conn: sqlite3.Connection, snapshot_id: int) -> list[dict]:
    return [
        dict(r)
        for r in conn.execute(
            """
            SELECT e.Id AS EntryId, e.WeightFraction,
                   c.Label, c.ContextKey, c.Code AS CategoryCode,
                   c.Id AS AllocationCategoryId
            FROM AllocationEntry e
            JOIN AllocationCategory c ON c.Id = e.AllocationCategoryId
            WHERE e.AllocationSnapshotId = ?
            ORDER BY e.WeightFraction DESC, c.Label
            """,
            (snapshot_id,),
        ).fetchall()
    ]


def get_disclosure_detail(conn: sqlite3.Connection, snapshot_id: int) -> dict:
    snapshot = conn.execute(
        """
        SELECT s.Id AS SnapshotId, s.AllocationAsOfDate, s.BasisNote,
               s.CoverageStatus, s.SourceLocator,
               e.Id AS ETFId, e.FundName,
               d.DimensionName,
               doc.Url, doc.CapturedFileRef, doc.RetrievedAt
        FROM AllocationSnapshot s
        JOIN ETF                 e   ON e.Id = s.ETFId
        JOIN AllocationDimension d   ON d.Id = s.AllocationDimensionId
        JOIN SourceDocument      doc ON doc.Id = s.SourceDocumentId
        WHERE s.Id = ?
        """,
        (snapshot_id,),
    ).fetchone()
    if snapshot is None:
        raise NotFoundError(f"Disclosure {snapshot_id} not found.")
    result = dict(snapshot)
    result["Entries"] = get_allocation_entries(conn, snapshot_id)
    return result


def get_customer_portfolio(conn: sqlite3.Connection, customer_number: str) -> dict:
    customer = conn.execute(
        "SELECT Id, CustomerNumber, GivenName, FamilyName, Email "
        "FROM Customer WHERE CustomerNumber = ?",
        (customer_number,),
    ).fetchone()
    if customer is None:
        raise NotFoundError(f"Customer {customer_number} not found.")

    portfolio = conn.execute(
        """
        SELECT Id, PortfolioReference, PortfolioName, BaseCurrency
        FROM Portfolio WHERE CustomerId = ?
        """,
        (customer["Id"],),
    ).fetchone()
    if portfolio is None:
        raise BusinessRuleError(f"Customer {customer_number} has no portfolio.")

    holdings = [
        dict(r)
        for r in conn.execute(
            """
            SELECT h.Id AS HoldingId, h.WeightFraction, h.HoldingAsOfDate,
                   (SELECT i.IdentifierValue FROM ETFIdentifier i
                      WHERE i.ETFId = h.ETFId AND i.IdentifierScheme = 'Ticker'
                      LIMIT 1) AS Ticker,
                   e.FundName
            FROM Holding h
            JOIN ETF e ON e.Id = h.ETFId
            WHERE h.PortfolioId = ?
            ORDER BY h.WeightFraction DESC
            """,
            (portfolio["Id"],),
        ).fetchall()
    ]
    result = dict(customer)
    result["Portfolio"] = dict(portfolio)
    result["Holdings"] = holdings
    return result


# ===========================================================================
# WRITES (validated transactions)
# ===========================================================================
def create_disclosure(conn: sqlite3.Connection, payload: dict) -> dict:
    """Create a snapshot and its entries atomically.

    payload keys: ETFId, AllocationDimensionId, SourceDocumentId,
    AllocationAsOfDate, BasisNote, CoverageStatus, SourceLocator,
    Entries: [{"AllocationCategoryId": int, "WeightFraction": float}, ...]
    """
    entries = payload.get("Entries")
    if not entries:
        raise BusinessRuleError("A saved disclosure must contain at least one entry.")

    validated = []
    for entry in entries:
        validated.append(
            (entry["AllocationCategoryId"],
             _validate_weight(entry.get("WeightFraction")))
        )

    try:
        with validated_transaction(conn):
            cur = conn.execute(
                """
                INSERT INTO AllocationSnapshot
                    (ETFId, AllocationDimensionId, SourceDocumentId,
                     AllocationAsOfDate, BasisNote, CoverageStatus, SourceLocator)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload["ETFId"],
                    payload["AllocationDimensionId"],
                    payload["SourceDocumentId"],
                    payload["AllocationAsOfDate"],
                    payload["BasisNote"],
                    payload.get("CoverageStatus", "Complete"),
                    payload["SourceLocator"],
                ),
            )
            snapshot_id = cur.lastrowid
            for category_id, weight in validated:
                conn.execute(
                    """
                    INSERT INTO AllocationEntry
                        (AllocationSnapshotId, AllocationCategoryId, WeightFraction)
                    VALUES (?, ?, ?)
                    """,
                    (snapshot_id, category_id, weight),
                )
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc

    return get_disclosure_detail(conn, snapshot_id)


def update_entry_weight(
    conn: sqlite3.Connection, entry_id: int, new_weight: Any
) -> dict:
    """Update one entry's weight. A Complete total that breaks is rejected."""
    weight = _validate_weight(new_weight)
    if conn.execute(
        "SELECT Id FROM AllocationEntry WHERE Id = ?", (entry_id,)
    ).fetchone() is None:
        raise NotFoundError(f"Entry {entry_id} not found.")

    try:
        with validated_transaction(conn):
            conn.execute(
                "UPDATE AllocationEntry SET WeightFraction = ? WHERE Id = ?",
                (weight, entry_id),
            )
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc

    return dict(
        conn.execute(
            """
            SELECT e.Id AS EntryId, e.AllocationSnapshotId, e.WeightFraction,
                   c.Label, c.Id AS AllocationCategoryId
            FROM AllocationEntry e
            JOIN AllocationCategory c ON c.Id = e.AllocationCategoryId
            WHERE e.Id = ?
            """,
            (entry_id,),
        ).fetchone()
    )


def update_weights_batch(
    conn: sqlite3.Connection, changes: list[dict]
) -> list[dict]:
    """Update several entries in one transaction (keeps Complete totals valid).

    changes: [{"EntryId": int, "WeightFraction": float}, ...]
    """
    if not changes:
        raise ValidationError("No changes supplied.")
    normalized = []
    for change in changes:
        normalized.append(
            (change["EntryId"],
             _validate_weight(change.get("WeightFraction")))
        )

    try:
        with validated_transaction(conn):
            for entry_id, weight in normalized:
                conn.execute(
                    "UPDATE AllocationEntry SET WeightFraction = ? WHERE Id = ?",
                    (weight, entry_id),
                )
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc

    return [
        dict(
            conn.execute(
                """
                SELECT e.Id AS EntryId, e.AllocationSnapshotId, e.WeightFraction,
                       c.Label
                FROM AllocationEntry e
                JOIN AllocationCategory c ON c.Id = e.AllocationCategoryId
                WHERE e.Id = ?
                """,
                (entry_id,),
            ).fetchone()
        )
        for entry_id, _ in normalized
    ]


def delete_entry(conn: sqlite3.Connection, entry_id: int) -> dict:
    """Delete an entry; the last entry of a snapshot cannot be removed."""
    existing = conn.execute(
        "SELECT Id, AllocationSnapshotId FROM AllocationEntry WHERE Id = ?",
        (entry_id,),
    ).fetchone()
    if existing is None:
        raise NotFoundError(f"Entry {entry_id} not found.")

    try:
        with validated_transaction(conn):
            conn.execute(
                "DELETE FROM AllocationEntry WHERE Id = ?", (entry_id,)
            )
    except ModelIntegrityError as exc:
        raise BusinessRuleError(str(exc)) from exc

    return {
        "DeletedEntryId": entry_id,
        "AllocationSnapshotId": existing["AllocationSnapshotId"],
    }
