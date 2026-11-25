"""Shared M5 startup for the quickstart, CRUD demo and graph-backed application.

The lower-level GraphDatabase remains usable for isolated migration tests. Real
entry points use this factory so Mason's validator cannot be omitted by accident.
"""

from pathlib import Path

from dal.models.semantic.backend_bridge import make_backend_validator

from .store import GraphDatabase
from .vocabulary import ROOT

DEFAULT_ONTOLOGY = ROOT / "src/dal/models/semantic/etf_allocations.owl"


def open_graph_database(path=None, *, capture_root=ROOT, ontology_path=DEFAULT_ONTOLOGY):
    """Open a validated graph and load the ontology into its separate named graph.

    Both the accepted M4 parity checks and the native graph checks run on existing
    data and on every staged write. No reasoner or inferred triples are installed.
    The caller must share this one instance across application request threads.
    """
    ontology_path = Path(ontology_path)
    if not ontology_path.is_file():
        raise FileNotFoundError(f"Ontology file not found: {ontology_path}")
    graph = GraphDatabase(
        path,
        validator=make_backend_validator(capture_root=capture_root),
        capture_root=capture_root,
    )
    # Reject invalid existing data before replacing even the ontology graph.
    graph.validate(graph._store)
    graph.load_ontology(ontology_path)
    return graph
