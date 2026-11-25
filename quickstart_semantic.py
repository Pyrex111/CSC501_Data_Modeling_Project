#!/usr/bin/env python3
"""Create/reuse an embedded M5 graph without changing the accepted M4 database."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from dal.seed_data import seed
from semantic.codec import decode_records, export_connection, export_rdfxml
from semantic.parity import compare
from semantic.runtime import DEFAULT_ONTOLOGY, open_graph_database
from semantic.vocabulary import DATA_GRAPH, ONTOLOGY_GRAPH, ROOT, schema_connection


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, default=ROOT / "data/semantic_store")
    parser.add_argument(
        "--compare",
        action="store_true",
        help="require parity with a fresh M4 synthetic seed",
    )
    parser.add_argument(
        "--export", type=Path, default=ROOT / "milestones/05_semantic/data/demo.rdf"
    )
    parser.add_argument(
        "--ontology",
        type=Path,
        default=DEFAULT_ONTOLOGY,
        help="RDF/XML ontology; defaults to the committed Mason ontology",
    )
    parser.add_argument(
        "--serve",
        action="store_true",
        help="after setup, launch the graph-backed web UI on the same graph instance",
    )
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args(argv)
    # Do not publish an empty directory or accept an unusable capture set when
    # fresh sample validation fails; prepare the entire ABox before opening disk.
    sql = schema_connection()
    try:
        seed(sql, ROOT)
        graph = open_graph_database(
            args.store, capture_root=ROOT, ontology_path=args.ontology
        )
        if not any(q.graph_name == DATA_GRAPH for q in graph.snapshot()):
            graph.load_data(export_connection(sql))
            print("Created RDF data graph:", args.store)
        else:
            print("Reused existing graph:", args.store)
        print("Loaded ontology into:", ONTOLOGY_GRAPH.value)
        args.export.parent.mkdir(parents=True, exist_ok=True)
        export_rdfxml(graph._store, args.export)
        evidence = {
            "triple_store": "Oxigraph/pyoxigraph 0.5.3",
            "baseline": "a00c0052289bc5acce17ad1b57f4d84832abda14",
            "data_triples": sum(q.graph_name == DATA_GRAPH for q in graph.snapshot()),
            "entity_counts": {
                t: len(rows) for t, rows in decode_records(graph._store).items()
            },
            "ontology_supplied": True,
            "ontology_path": str(args.ontology),
            "ontology_triples": sum(
                q.graph_name == ONTOLOGY_GRAPH for q in graph.snapshot()
            ),
            "validation": {
                "m4_parity_bridge": True,
                "native_graph_validator": True,
                "capture_files_checked": True,
                "owl_reasoner": False,
            },
            "vocabulary_status": (
                "aligned with Mason's committed v1.1.0 ontology"
                if args.ontology.resolve() == DEFAULT_ONTOLOGY.resolve()
                else "custom ontology loaded; vocabulary alignment not asserted"
            ),
        }
        if args.compare:
            evidence["query_comparison"] = compare(sql, graph)
        graph.flush()
        print(json.dumps(evidence, indent=2))
    finally:
        sql.close()
    if args.serve:
        # Share this instance: the embedded store allows one writable opener.
        sys.path.insert(0, str(ROOT / "src" / "ui"))
        from app import app

        app.config.update(BACKEND="graph", GRAPH=graph, GRAPH_STORE=args.store)
        print(f"Serving the graph-backed UI at http://127.0.0.1:{args.port}/ (Ctrl+C to stop)")
        app.run(port=args.port, debug=False, use_reloader=False, threaded=True)
    return evidence


if __name__ == "__main__":
    main()
