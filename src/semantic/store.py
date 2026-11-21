"""Embedded persistent Oxigraph with staged validation and atomic publication.

One GraphDatabase instance per process, shared by all request threads.
RocksDB owns the on-disk writer lock; do not run multiple Flask workers.
"""

from threading import RLock

from pyoxigraph import RdfFormat, Store

from dal.schema_validation import ModelIntegrityError

from .codec import validate_m4_parity
from .terms import value
from .vocabulary import DATA_GRAPH, ONTOLOGY_GRAPH, PREFIXES


def select(store, query, bindings=None):
    results = store.query(query, prefixes=PREFIXES, substitutions=bindings)
    names = [v.value for v in results.variables]
    return [{name: value(row[i]) for i, name in enumerate(names)} for row in results]


def block(quads, graph=DATA_GRAPH):
    return (
        f"GRAPH {graph} {{\n"
        + "\n".join(f"{q.subject} {q.predicate} {q.object} ." for q in quads)
        + "\n}"
    )


class GraphDatabase:
    def __init__(self, path=None, *, validator=None, capture_root=None):
        self._store = Store(path)
        self._lock = RLock()
        self.validator = validator  # Mason's candidate Store -> None or raise
        self.capture_root = capture_root

    def select(self, query, bindings=None):
        with self._lock:
            return select(self._store, query, bindings)

    def snapshot(self):
        with self._lock:
            return frozenset(self._store)

    def validate(self, candidate):
        validate_m4_parity(candidate, capture_root=self.capture_root)
        if self.validator is not None:
            if self.validator(candidate) is not None:
                raise ModelIntegrityError(
                    "Shared validator must return None or raise on failure"
                )

    def mutate(self, operation):
        """Run operation(candidate), validate, publish one exact SPARQL delta.

        All application writers must use this method. Validation failure or an
        operation error never changes the live graph. Candidate construction,
        ID allocation, validation and publication share one reentrant lock.
        """
        with self._lock:
            before = frozenset(self._store)
            candidate = Store()
            candidate.extend(before)
            result = operation(candidate)
            after = frozenset(candidate)

            def outside(qs):
                return {q for q in qs if q.graph_name != DATA_GRAPH}

            if outside(before) != outside(after):
                raise ModelIntegrityError(
                    "Application writes may change only the data graph"
                )
            self.validate(candidate)
            if frozenset(candidate) != after:
                raise ModelIntegrityError(
                    "Validators must inspect the candidate without mutating it"
                )
            removed, added = before - after, after - before
            requests = []
            if removed:
                requests.append("DELETE DATA { " + block(removed) + " }")
            if added:
                requests.append("INSERT DATA { " + block(added) + " }")
            if requests:
                self._store.update(";\n".join(requests))
            return result

    def load_data(self, quads):
        quads = list(quads)

        def load(candidate):
            if any(candidate.quads_for_pattern(None, None, None, DATA_GRAPH)):
                raise FileExistsError(
                    "Data graph already populated; use a new store directory"
                )
            candidate.extend(quads)

        self.mutate(load)

    def flush(self):
        self._store.flush()

    def load_ontology(self, path):
        """Setup-only atomic replacement of the TBox; no inference is enabled."""
        parsed = Store()
        parsed.load(path=path, format=RdfFormat.RDF_XML, to_graph=ONTOLOGY_GRAPH)
        with self._lock:
            self._store.update(
                f"CLEAR SILENT GRAPH {ONTOLOGY_GRAPH}; INSERT DATA {{ "
                + block(parsed, ONTOLOGY_GRAPH)
                + " }"
            )
