"""Proposed integration vocabulary, not Mason's final ontology or FIBO mapping.

Keep all identity/property choices here. Integer record IDs support the existing
UI; resource IRIs identify the migrated records and are not business keys.
"""

import sqlite3
from pathlib import Path

from pyoxigraph import NamedNode

ROOT = Path(__file__).resolve().parents[2]
BASE = "https://github.com/Pyrex111/CSC501_Data_Modeling_Project/"
NS = BASE + "ontology#"
RESOURCE = BASE + "resource/"
DATA_GRAPH = NamedNode(BASE + "graph/data")
ONTOLOGY_GRAPH = NamedNode(BASE + "graph/ontology")
RDF_TYPE = NamedNode("http://www.w3.org/1999/02/22-rdf-syntax-ns#type")
XSD = "http://www.w3.org/2001/XMLSchema#"
PREFIXES = {"etf": NS, "xsd": XSD}
# (source entity, FK column) -> proposed semantic relationship.
OBJECT_PROPERTIES = {
    ("Portfolio", "CustomerId"): "ownedBy",
    ("ETF", "ETFProviderId"): "offeredBy",
    ("ETFIdentifier", "ETFId"): "identifiesETF",
    ("Holding", "PortfolioId"): "inPortfolio",
    ("Holding", "ETFId"): "holdsETF",
    ("SourceDocument", "ETFProviderId"): "publishedBy",
    ("AllocationCategory", "AllocationDimensionId"): "hasDimension",
    ("AllocationCategory", "ClassificationSchemeId"): "definedBy",
    ("AllocationSnapshot", "ETFId"): "describesETF",
    ("AllocationSnapshot", "AllocationDimensionId"): "hasDimension",
    ("AllocationSnapshot", "SourceDocumentId"): "supportedBy",
    ("AllocationEntry", "AllocationSnapshotId"): "inSnapshot",
    ("AllocationEntry", "AllocationCategoryId"): "usesCategory",
}


def schema_connection():
    db = sqlite3.connect(":memory:", isolation_level=None)
    db.row_factory = sqlite3.Row
    db.executescript((ROOT / "src/dal/sql/schema.sql").read_text())
    return db


def schema_metadata():
    """Read the accepted schema; do not maintain a second handwritten dictionary."""
    db = schema_connection()
    try:
        tables = [
            r[0]
            for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        ]
        return {
            table: {
                "columns": [
                    dict(r) for r in db.execute(f'PRAGMA table_info("{table}")')
                ],
                "foreign_keys": {
                    r["from"]: r["table"]
                    for r in db.execute(f'PRAGMA foreign_key_list("{table}")')
                },
            }
            for table in tables
        }
    finally:
        db.close()


SCHEMA = schema_metadata()


def predicate(table, column):
    local = OBJECT_PROPERTIES.get((table, column))
    return NamedNode(
        NS
        + (local or ("recordId" if column == "Id" else column[0].lower() + column[1:]))
    )


def datatype(column):
    name = column["name"]
    if column["type"] == "INTEGER":
        return NamedNode(XSD + "integer")
    if column["type"] == "REAL":
        return NamedNode(XSD + "double")
    if name.endswith("Date"):
        return NamedNode(XSD + "date")
    if name in ("RetrievedAt", "PublishedAt"):
        return NamedNode(XSD + "dateTime")
    return NamedNode(XSD + "string")


def resource(table, record_id):
    if (
        table not in SCHEMA
        or isinstance(record_id, bool)
        or not isinstance(record_id, int)
    ):
        raise ValueError("A known entity and integer record ID are required")
    return NamedNode(f"{RESOURCE}{table}/{record_id}")
