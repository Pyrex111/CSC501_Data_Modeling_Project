"""Read-only lookup queries that fill the UI's form controls (Shahmeer).

repositories.py (Mason) covers disclosures and portfolios; the forms also need
plain lists of ETFs, dimensions, source documents, categories and customers.
These helpers are kept in the DAL so the UI never writes SQL. Every query is
parameterized and returns plain dicts.
"""
from __future__ import annotations

import sqlite3

_TICKER = """(SELECT i.IdentifierValue FROM ETFIdentifier i
               WHERE i.ETFId = e.Id AND i.IdentifierScheme = 'Ticker'
               ORDER BY i.ExchangeContext, i.IdentifierValue LIMIT 1)"""


def list_etfs(conn: sqlite3.Connection) -> list[dict]:
    sql = f"SELECT e.Id AS ETFId, e.FundName, {_TICKER} AS Ticker FROM ETF e ORDER BY Ticker"
    return [dict(r) for r in conn.execute(sql).fetchall()]


def list_dimensions(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT Id AS DimensionId, DimensionName FROM AllocationDimension ORDER BY Id"
    ).fetchall()]


def list_source_documents(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute(
        """
        SELECT d.Id AS SourceDocumentId, d.DocumentTitle, d.Url, d.RetrievedAt,
               p.LegalName AS ProviderName
        FROM SourceDocument d
        JOIN ETFProvider p ON p.Id = d.ETFProviderId
        ORDER BY d.Id
        """
    ).fetchall()]


def list_categories(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute(
        """
        SELECT c.Id AS CategoryId, c.AllocationDimensionId, c.Label, c.Code,
               c.ContextKey, cs.SchemeName, cs.Version
        FROM AllocationCategory c
        LEFT JOIN ClassificationScheme cs ON cs.Id = c.ClassificationSchemeId
        ORDER BY c.AllocationDimensionId, c.Label, c.Id
        """
    ).fetchall()]


def list_customers(conn: sqlite3.Connection) -> list[dict]:
    return [dict(r) for r in conn.execute(
        "SELECT CustomerNumber, GivenName, FamilyName FROM Customer ORDER BY CustomerNumber"
    ).fetchall()]


def list_customer_portfolios(conn: sqlite3.Connection, customer_number: str) -> list[dict]:
    return [dict(r) for r in conn.execute(
        """
        SELECT p.Id AS PortfolioId, p.PortfolioReference, p.PortfolioName
        FROM Portfolio p JOIN Customer c ON c.Id = p.CustomerId
        WHERE c.CustomerNumber = ?
        ORDER BY p.PortfolioReference
        """,
        (customer_number,),
    ).fetchall()]


def list_holding_dates(conn: sqlite3.Connection, portfolio_id: int) -> list[str]:
    return [r[0] for r in conn.execute(
        "SELECT DISTINCT HoldingAsOfDate FROM Holding WHERE PortfolioId = ? "
        "ORDER BY HoldingAsOfDate DESC",
        (portfolio_id,),
    ).fetchall()]
