"""Adapter that lets the accepted graph backend call this validator as its hook.

The backend contract in ``milestones/05_semantic/docs/integration_contract.md``
expects a callable handed to ``GraphDatabase(path, validator=...)``. That callable
receives the *candidate* pyoxigraph ``Store`` (the whole dataset, not only the data
graph), must inspect it without mutating it, return ``None`` on success, and raise
``ModelIntegrityError`` with an actionable message on failure.

This module projects the candidate's data graph into rdflib terms and runs exactly
the same rule set as the CLI, so a rule proved by a test is also the rule applied
on the write path. The ontology graph is deliberately ignored: TBox axioms are not
ABox assertions, and no reasoner is enabled by the backend.

Owner: Mason Li, with AI assistance disclosed in the contribution notes.
"""
from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

from rdflib import BNode, Graph, Literal, URIRef

from dal.schema_validation import ModelIntegrityError

from .graph_validation import collect_issues

DATA_GRAPH = "https://github.com/Pyrex111/CSC501_Data_Modeling_Project/graph/data"


def _to_rdflib(node):
    """Map a pyoxigraph term to its rdflib equivalent without importing at module load."""
    kind = type(node).__name__
    if kind == "NamedNode":
        return URIRef(node.value)
    if kind == "BlankNode":
        return BNode(node.value)
    if kind == "Literal":
        datatype = URIRef(node.datatype.value) if node.datatype is not None else None
        return Literal(node.value, datatype=datatype, lang=node.language)
    raise TypeError(f"unsupported RDF term type: {kind}")


def graph_from_quads(quads: Iterable) -> Graph:
    """Build a read-only rdflib graph from quads (used by tests and by the hook)."""
    graph = Graph()
    for quad in quads:
        graph.add((_to_rdflib(quad.subject),
                   _to_rdflib(quad.predicate),
                   _to_rdflib(quad.object)))
    return graph


def graph_from_store(store, *, graph_iri: str = DATA_GRAPH) -> Graph:
    """Read the ABox out of a pyoxigraph Store without touching it."""
    from pyoxigraph import NamedNode  # local import: only needed on the backend path

    return graph_from_quads(
        store.quads_for_pattern(None, None, None, NamedNode(graph_iri))
    )


def validate_candidate_store(store, *, capture_root: Path | str | None = None) -> None:
    """Backend hook: raise ModelIntegrityError listing every graph-rule violation."""
    issues = collect_issues(graph_from_store(store), capture_root=capture_root)
    if issues:
        raise ModelIntegrityError("\n".join(issues))


def make_backend_validator(*, capture_root: Path | str | None = None) -> Callable:
    """Bind capture_root once, for ``GraphDatabase(..., validator=make_backend_validator(...))``."""

    def validate(store) -> None:
        validate_candidate_store(store, capture_root=capture_root)

    return validate
