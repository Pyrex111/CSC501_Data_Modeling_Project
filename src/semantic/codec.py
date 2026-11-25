"""Lossless migration of accepted M4 records; explicit RDF literals and edges."""

import sqlite3
from collections import defaultdict

from pyoxigraph import Literal, NamedNode, Quad, RdfFormat

from dal.schema_validation import ModelIntegrityError, validate_database

from .terms import value
from .vocabulary import (
    DATA_GRAPH,
    NS,
    RDF_TYPE,
    SCHEMA,
    datatype,
    predicate,
    resource,
    schema_connection,
)


def record_quads(table, row):
    subject = resource(table, row["Id"])
    yield Quad(subject, RDF_TYPE, NamedNode(NS + table), DATA_GRAPH)
    for column in SCHEMA[table]["columns"]:
        name = column["name"]
        value = row.get(name)
        if value is None:
            continue  # absence is unknown, never a fabricated literal
        target = SCHEMA[table]["foreign_keys"].get(name)
        obj = (
            resource(target, value)
            if target
            else Literal(str(value), datatype=datatype(column))
        )
        yield Quad(subject, predicate(table, name), obj, DATA_GRAPH)


def export_connection(connection):
    connection.row_factory = sqlite3.Row
    for table in SCHEMA:
        for row in connection.execute(f'SELECT * FROM "{table}" ORDER BY Id'):
            yield from record_quads(table, dict(row))


def decode_records(store):
    """Reject ambiguous/lossy ABox shapes instead of silently discarding triples."""
    grouped = defaultdict(lambda: defaultdict(list))
    for q in store.quads_for_pattern(None, None, None, DATA_GRAPH):
        grouped[q.subject][q.predicate].append(q.object)
    classes = {NamedNode(NS + t): t for t in SCHEMA}
    records = {t: [] for t in SCHEMA}
    identities = {}
    for subject, properties in grouped.items():
        types = properties.get(RDF_TYPE, [])
        if len(types) != 1 or types[0] not in classes:
            raise ModelIntegrityError(
                f"{subject}: exactly one supported explicit entity class is required"
            )
        table = classes[types[0]]
        row = {}
        spec = SCHEMA[table]
        known = {RDF_TYPE} | {predicate(table, c["name"]) for c in spec["columns"]}
        if set(properties) - known:
            raise ModelIntegrityError(
                f"{subject}: unmapped properties would be lost by validation"
            )
        for col in spec["columns"]:
            name = col["name"]
            values = properties.get(predicate(table, name), [])
            if len(values) > 1 or (not values and (col["notnull"] or col["pk"])):
                raise ModelIntegrityError(f"{subject}: invalid cardinality for {name}")
            if not values:
                row[name] = None
                continue
            obj = values[0]
            if name in spec["foreign_keys"]:
                if not isinstance(obj, NamedNode):
                    raise ModelIntegrityError(
                        f"{subject}: {name} requires a resource IRI"
                    )
                row[name] = obj
            else:
                if (
                    not isinstance(obj, Literal)
                    or obj.datatype != datatype(col)
                    or obj.language is not None
                ):
                    raise ModelIntegrityError(
                        f"{subject}: incorrect literal datatype for {name}"
                    )
                try:
                    row[name] = value(obj)
                except ValueError as exc:
                    raise ModelIntegrityError(f"{subject}: invalid {name}") from exc
        if subject != resource(table, row["Id"]):
            raise ModelIntegrityError(f"{subject}: IRI and record ID disagree")
        identities[subject] = (table, row["Id"])
        records[table].append(row)
    for table, rows in records.items():
        for row in rows:
            for fk, target in SCHEMA[table]["foreign_keys"].items():
                obj = row[fk]
                if obj is None:
                    continue
                identity = identities.get(obj)
                if identity is None or identity[0] != target:
                    raise ModelIntegrityError(
                        f"{table} {row['Id']}: {fk} has missing/wrong-class target"
                    )
                row[fk] = identity[1]
    return records


def validate_m4_parity(store, *, capture_root=None):
    """Temporary closed-world bridge pending Mason's native graph validator.

    Persistence, retrieval and writes use RDF/SPARQL. Only this isolated checker
    projects the candidate graph into an ephemeral accepted SQL schema, preserving
    every mapped fact and reusing its identity/scalar/context/total rules.
    """
    records = decode_records(store)
    db = schema_connection()
    try:
        db.execute("BEGIN")
        for table, rows in records.items():
            names = [c["name"] for c in SCHEMA[table]["columns"]]
            sql = f'INSERT INTO "{table}" ({", ".join(names)}) VALUES ({", ".join("?" for _ in names)})'
            db.executemany(sql, [[row[n] for n in names] for row in rows])
        validate_database(db, capture_root=capture_root)
    except sqlite3.IntegrityError as exc:
        raise ModelIntegrityError(str(exc)) from exc
    finally:
        db.close()


def export_rdfxml(store, path):
    store.dump(output=path, format=RdfFormat.RDF_XML, from_graph=DATA_GRAPH)
