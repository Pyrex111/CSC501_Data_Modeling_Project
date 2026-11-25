"""Verify the actual M5 startup and write paths with Mason's validator attached."""

import contextlib
import gc
import io
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT)]

from dal.models.semantic import backend_bridge
from dal.schema_validation import ModelIntegrityError
from semantic import repositories as repo
from semantic.codec import export_connection
from semantic.runtime import open_graph_database
from semantic.vocabulary import DATA_GRAPH, NS, ONTOLOGY_GRAPH, resource, schema_connection
from test_relational_schema import fixture
from quickstart_semantic import main as quickstart


class SemanticRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.sql = schema_connection()
        fixture(self.sql)
        self.graph = open_graph_database(capture_root=ROOT)
        self.graph.load_data(export_connection(self.sql))

    def tearDown(self):
        self.sql.close()
        self.graph = None
        gc.collect()

    def payload(self):
        return {
            "ETFId": 1, "AllocationDimensionId": 1, "SourceDocumentId": 1,
            "AllocationAsOfDate": "2026-11-02", "BasisNote": "Synthetic integration",
            "SourceLocator": "runtime-sector-block", "CoverageStatus": "Complete",
            "Entries": [
                {"AllocationCategoryId": 1, "WeightFraction": 0.3},
                {"AllocationCategoryId": 2, "WeightFraction": 0.7},
            ],
        }

    def assert_rejected_unchanged(self, operation):
        before = self.graph.snapshot()
        with self.assertRaises((repo.BusinessRuleError, ModelIntegrityError)):
            operation()
        self.assertEqual(self.graph.snapshot(), before)

    def test_default_startup_loads_tbox_and_preserves_abox_without_inference(self):
        from pyoxigraph import Store
        expected = Store()
        expected.extend(export_connection(self.sql))
        snapshot = self.graph.snapshot()
        self.assertTrue(any(q.graph_name == ONTOLOGY_GRAPH for q in snapshot))
        self.assertEqual(
            {q for q in snapshot if q.graph_name == DATA_GRAPH},
            set(expected),
        )
        self.assertTrue(callable(self.graph.validator))

    def test_repository_create_batch_and_delete_invoke_native_validator(self):
        with patch.object(
            backend_bridge, "validate_candidate_store",
            wraps=backend_bridge.validate_candidate_store,
        ) as validator:
            detail = repo.create_disclosure(self.graph, self.payload())
            first, second = [e["EntryId"] for e in detail["Entries"]]
            repo.update_weights_batch(self.graph, [
                {"EntryId": first, "WeightFraction": 0.4},
                {"EntryId": second, "WeightFraction": 0.6},
            ])
            payload = self.payload()
            payload.update(CoverageStatus="Partial", SourceLocator="runtime-partial")
            partial = repo.create_disclosure(self.graph, payload)
            repo.delete_entry(self.graph, partial["Entries"][0]["EntryId"])
            self.assertEqual(validator.call_count, 4)
            self.assertTrue(all(
                call.kwargs["capture_root"] == ROOT for call in validator.call_args_list
            ))

    def test_native_validator_rejects_bad_total_even_without_legacy_bridge(self):
        payload = self.payload()
        payload["Entries"][1]["WeightFraction"] = 0.1
        with patch("semantic.store.validate_m4_parity"):
            self.assert_rejected_unchanged(
                lambda: repo.create_disclosure(self.graph, payload)
            )

    def test_native_validator_rejects_edit_and_deletion_without_legacy_bridge(self):
        with patch("semantic.store.validate_m4_parity"):
            self.assert_rejected_unchanged(
                lambda: repo.update_entry_weight(self.graph, 1, 0.1)
            )
            self.assert_rejected_unchanged(lambda: repo.delete_entry(self.graph, 1))
            # A valid partial state still requires its final entry.
            self.graph.mutate(lambda store: store.update(f'''
                DELETE DATA {{ GRAPH {DATA_GRAPH} {{
                  {resource("AllocationSnapshot", 1)} <{NS}coverageStatus> "Complete"
                }} }};
                INSERT DATA {{ GRAPH {DATA_GRAPH} {{
                  {resource("AllocationSnapshot", 1)} <{NS}coverageStatus> "Partial"
                }} }}
            '''))
            repo.delete_entry(self.graph, 1)
            self.assert_rejected_unchanged(lambda: repo.delete_entry(self.graph, 2))

    def test_native_validator_checks_capture_files_on_write(self):
        with patch("semantic.store.validate_m4_parity"):
            self.assert_rejected_unchanged(lambda: self.graph.mutate(
                lambda store: store.update(f'''
                    DELETE {{ GRAPH {DATA_GRAPH} {{
                      {resource("SourceDocument", 1)} <{NS}capturedFileRef> ?old
                    }} }}
                    INSERT {{ GRAPH {DATA_GRAPH} {{
                      {resource("SourceDocument", 1)} <{NS}capturedFileRef> "missing.pdf"
                    }} }}
                    WHERE {{ GRAPH {DATA_GRAPH} {{
                      {resource("SourceDocument", 1)} <{NS}capturedFileRef> ?old
                    }} }}
                ''')
            ))

    def test_missing_ontology_fails_before_creating_persistent_store(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store"
            with self.assertRaises(FileNotFoundError):
                open_graph_database(path, ontology_path=Path(directory) / "missing.owl")
            self.assertFalse(path.exists())

    def test_existing_invalid_graph_rejected_before_ontology_replacement(self):
        from pyoxigraph import Literal, NamedNode, Quad, Store
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "store"
            store = Store(str(path))
            store.extend(export_connection(self.sql))
            store.add(Quad(
                resource("AllocationEntry", 1), NamedNode(NS + "weightFraction"),
                Literal(0.9), DATA_GRAPH,
            ))
            before = frozenset(store)
            store.flush()
            del store
            gc.collect()
            with patch("semantic.store.validate_m4_parity"):
                with self.assertRaises(ModelIntegrityError):
                    open_graph_database(path)
            gc.collect()
            store = Store(str(path))
            self.assertEqual(frozenset(store), before)
            del store

    def test_quickstart_defaults_load_ontology_validate_reuse_and_match_sql(self):
        with tempfile.TemporaryDirectory() as directory:
            args = ["--store", str(Path(directory) / "store"), "--compare",
                    "--export", str(Path(directory) / "demo.rdf")]
            with contextlib.redirect_stdout(io.StringIO()):
                first = quickstart(args)
                gc.collect()
                second = quickstart(args)
            self.assertEqual(first["data_triples"], 356)
            self.assertEqual(first["entity_counts"], second["entity_counts"])
            self.assertGreater(first["ontology_triples"], 0)
            self.assertTrue(first["validation"]["native_graph_validator"])
            self.assertTrue(first["validation"]["capture_files_checked"])
            self.assertTrue(all(q["full_result_match"] for q in second["query_comparison"]))

    def test_crud_demo_uses_integrated_runtime(self):
        from scripts.demo_semantic_crud import main
        with contextlib.redirect_stdout(io.StringIO()), patch.object(
            backend_bridge, "validate_candidate_store",
            wraps=backend_bridge.validate_candidate_store,
        ) as validator:
            events = main()
        self.assertGreater(validator.call_count, 0)
        self.assertEqual(sum(e["result"] == "saved" for e in events), 3)
        self.assertEqual(sum("graph unchanged" in e["result"] for e in events), 3)


if __name__ == "__main__":
    unittest.main()
