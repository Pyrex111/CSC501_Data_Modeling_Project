"""Validate an ETF allocation RDF graph from the repository root.

Convenience wrapper so the CLI runs without setting ``PYTHONPATH``:

    py -3 scripts/validate_graph.py milestones/05_semantic/data/demo.rdf
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dal.models.semantic.graph_validation import main  # noqa: E402


if __name__ == "__main__":
    sys.exit(main())
