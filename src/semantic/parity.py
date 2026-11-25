"""Compare full result multisets of the six accepted SQL queries and SPARQL.

Numeric comparison allows 1e-10 for binary floating arithmetic. Datetime results
restore the accepted six-digit UTC representation. Missing bindings become None.
No SQL execution happens when answering the application's graph-backed reads.
"""

import json
from pathlib import Path

from dal.run_analysis_queries import QUERIES_FILE, _split

SPARQL_DIR = Path(__file__).resolve().parent / "sparql"


def normalized(row):
    return {k: round(v, 10) if isinstance(v, float) else v for k, v in row.items()}


def multiset(rows):
    return sorted(json.dumps(normalized(row), sort_keys=True) for row in rows)


def compare(connection, graph):
    statements = _split(QUERIES_FILE.read_text())
    files = sorted(SPARQL_DIR.glob("0*.sparql"))
    if len(statements) != 6 or len(files) != 6:
        raise RuntimeError("Expected exactly six SQL/SPARQL pairs")
    evidence = []
    for number, (sql, path) in enumerate(zip(statements, files), 1):
        sql_rows = [dict(r) for r in connection.execute(sql)]
        graph_rows = graph.select(path.read_text())
        equal = multiset(sql_rows) == multiset(graph_rows)
        evidence.append(
            {
                "query": number,
                "file": path.name,
                "sql_rows": len(sql_rows),
                "sparql_rows": len(graph_rows),
                "full_result_match": equal,
            }
        )
        if not equal:
            raise AssertionError(
                f"Q{number} mismatch:\nSQL={sql_rows}\nSPARQL={graph_rows}"
            )
    return evidence
