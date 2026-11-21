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
from semantic.store import GraphDatabase
from semantic.vocabulary import DATA_GRAPH, ONTOLOGY_GRAPH, ROOT, schema_connection


def main():
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
        help="Mason's RDF/XML ontology; retained in a separate graph",
    )
    args = parser.parse_args()
    # Do not publish an empty directory or accept an unusable capture set when
    # fresh sample validation fails; prepare the entire ABox before opening disk.
    sql = schema_connection()
    try:
        seed(sql, ROOT)
        graph = GraphDatabase(args.store, capture_root=ROOT)
        if not any(q.graph_name == DATA_GRAPH for q in graph.snapshot()):
            graph.load_data(export_connection(sql))
            print("Created RDF data graph:", args.store)
        else:
            graph.validate(graph._store)
            print("Reused existing graph:", args.store)
        if args.ontology:
            graph.load_ontology(args.ontology)
            print("Loaded supplied ontology into:", ONTOLOGY_GRAPH.value)
        args.export.parent.mkdir(parents=True, exist_ok=True)
        export_rdfxml(graph._store, args.export)
        evidence = {
            "triple_store": "Oxigraph/pyoxigraph 0.5.3",
            "baseline": "a00c0052289bc5acce17ad1b57f4d84832abda14",
            "data_triples": sum(q.graph_name == DATA_GRAPH for q in graph.snapshot()),
            "entity_counts": {
                t: len(rows) for t, rows in decode_records(graph._store).items()
            },
            "ontology_supplied": args.ontology is not None,
            "vocabulary_status": "proposed; Mason agreement pending",
        }
        if args.compare:
            evidence["query_comparison"] = compare(sql, graph)
        graph.flush()
        print(json.dumps(evidence, indent=2))
        return evidence
    finally:
        sql.close()


if __name__ == "__main__":
    main()
