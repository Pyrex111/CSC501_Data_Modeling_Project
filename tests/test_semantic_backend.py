# ruff: noqa: E402
# unittest discovery requires src on sys.path before application imports.
"""Graph migration, full-result parity, staged writes and persistence checks.

All records are fictional. These checks do not constitute ontology approval or
an end-user UI evaluation. Run with the existing unittest discovery command.
"""

import gc
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from pyoxigraph import Literal, NamedNode, Quad, RdfFormat, Store

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from test_relational_schema import fixture

from dal import lookups as sql_lookups
from dal import repositories as sql_repo
from dal.schema_validation import ModelIntegrityError
from dal.seed_data import seed
from semantic import lookups as graph_lookups
from semantic import repositories as graph_repo
from semantic.codec import decode_records, export_connection, export_rdfxml
from semantic.parity import compare
from semantic.store import GraphDatabase
from semantic.vocabulary import (
    DATA_GRAPH,
    NS,
    RDF_TYPE,
    SCHEMA,
    resource,
    schema_connection,
)


class SemanticBackendTests(unittest.TestCase):
    def setUp(self):
        self.sql = schema_connection()
        fixture(self.sql)
        self.graph = GraphDatabase(capture_root=ROOT)
        self.graph.load_data(export_connection(self.sql))

    def tearDown(self):
        self.sql.close()

    def payload(self, **overrides):
        result = {
            "ETFId": 1,
            "AllocationDimensionId": 1,
            "SourceDocumentId": 1,
            "AllocationAsOfDate": "2026-11-02",
            "BasisNote": "Synthetic test",
            "SourceLocator": "another-sector-block",
            "CoverageStatus": "Complete",
            "Entries": [
                {"AllocationCategoryId": 1, "WeightFraction": 0.3},
                {"AllocationCategoryId": 2, "WeightFraction": 0.7},
            ],
        }
        result.update(overrides)
        return result

    def partial(self):
        self.graph.mutate(
            lambda candidate: candidate.update(f"""
            DELETE {{ GRAPH {DATA_GRAPH} {{ {resource("AllocationSnapshot", 1)} <{NS}coverageStatus> ?old }} }}
            INSERT {{ GRAPH {DATA_GRAPH} {{ {resource("AllocationSnapshot", 1)} <{NS}coverageStatus> "Partial" }} }}
            WHERE {{ GRAPH {DATA_GRAPH} {{ {resource("AllocationSnapshot", 1)} <{NS}coverageStatus> ?old }} }}""")
        )

    def assert_unchanged(self, error, operation):
        before = self.graph.snapshot()
        with self.assertRaises(error):
            operation()
        self.assertEqual(self.graph.snapshot(), before)

    def test_roundtrip_preserves_every_record_and_nullable_value(self):
        decoded = decode_records(self.graph._store)
        for table in SCHEMA:
            expected = [
                dict(r)
                for r in self.sql.execute(f'SELECT * FROM "{table}" ORDER BY Id')
            ]
            self.assertEqual(sorted(decoded[table], key=lambda r: r["Id"]), expected)

    def test_rdfxml_roundtrip_preserves_graph_and_context_timestamps(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "data.rdf"
            export_rdfxml(self.graph._store, path)
            parsed = Store()
            parsed.load(path=path, format=RdfFormat.RDF_XML, to_graph=DATA_GRAPH)
            other = GraphDatabase(capture_root=ROOT)
            other.load_data(parsed)
            self.assertEqual(other.snapshot(), self.graph.snapshot())

    def test_search_and_detail_match_sql_contract(self):
        for filters in [
            {},
            {"ticker": "EXA"},
            {"dimension_name": "Geography"},
            {"etf_id": 1, "allocation_dimension_id": 2},
            {"as_of_date": "2026-10-31"},
            {"etf_id": 999},
        ]:
            self.assertEqual(
                graph_repo.search_disclosures(self.graph, **filters),
                sql_repo.search_disclosures(self.sql, **filters),
            )
        for sid in (1, 2):
            self.assertEqual(
                graph_repo.get_disclosure_detail(self.graph, sid),
                sql_repo.get_disclosure_detail(self.sql, sid),
            )

    def test_all_form_lookups_match_sql_contract(self):
        for name in [
            "list_etfs",
            "list_dimensions",
            "list_source_documents",
            "list_categories",
            "list_customers",
        ]:
            self.assertEqual(
                getattr(graph_lookups, name)(self.graph),
                getattr(sql_lookups, name)(self.sql),
            )
        self.assertEqual(
            graph_lookups.list_customer_portfolios(self.graph, "DEMO-C1"),
            sql_lookups.list_customer_portfolios(self.sql, "DEMO-C1"),
        )
        self.assertEqual(
            graph_lookups.list_holding_dates(self.graph, 1),
            sql_lookups.list_holding_dates(self.sql, 1),
        )

    def test_portfolio_contract_matches_sql(self):
        self.assertEqual(
            graph_repo.get_customer_portfolio(self.graph, "DEMO-C1"),
            sql_repo.get_customer_portfolio(self.sql, "DEMO-C1"),
        )

    def test_all_six_queries_match_complete_m4_result_multisets(self):
        sql = schema_connection()
        try:
            seed(sql, ROOT)
            graph = GraphDatabase(capture_root=ROOT)
            graph.load_data(export_connection(sql))
            evidence = compare(sql, graph)
            self.assertEqual([e["sparql_rows"] for e in evidence], [8, 2, 5, 5, 5, 17])
            self.assertTrue(all(e["full_result_match"] for e in evidence))
        finally:
            sql.close()

    def test_create_disclosure_returns_sql_compatible_result(self):
        self.assertEqual(
            graph_repo.create_disclosure(self.graph, self.payload()),
            sql_repo.create_disclosure(self.sql, self.payload()),
        )

    def test_create_bad_complete_total_leaves_graph_unchanged(self):
        payload = self.payload(
            Entries=[{"AllocationCategoryId": 1, "WeightFraction": 0.2}]
        )
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.create_disclosure(self.graph, payload),
        )

    def test_create_duplicate_business_identity_leaves_graph_unchanged(self):
        graph_repo.create_disclosure(self.graph, self.payload())
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.create_disclosure(self.graph, self.payload()),
        )

    def test_create_cross_dimension_or_missing_reference_is_rejected(self):
        for payload in [
            self.payload(ETFId=999),
            self.payload(Entries=[{"AllocationCategoryId": 3, "WeightFraction": 1.0}]),
        ]:
            self.assert_unchanged(
                graph_repo.BusinessRuleError,
                lambda payload=payload: graph_repo.create_disclosure(
                    self.graph, payload
                ),
            )

    def test_unknown_classification_cannot_cross_disclosure_block(self):
        payload = self.payload(
            AllocationDimensionId=2,
            Entries=[
                {"AllocationCategoryId": 3, "WeightFraction": 0.6},
                {"AllocationCategoryId": 4, "WeightFraction": 0.4},
            ],
        )
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.create_disclosure(self.graph, payload),
        )

    def test_invalid_weight_edit_rolls_back(self):
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.update_entry_weight(self.graph, 1, 0.1),
        )
        for invalid in [float("nan"), float("inf"), -0.1, 1.1]:
            self.assert_unchanged(
                graph_repo.ValidationError,
                lambda invalid=invalid: graph_repo.update_entry_weight(
                    self.graph, 1, invalid
                ),
            )

    def test_coherent_batch_preserves_complete_total(self):
        changes = [
            {"EntryId": 1, "WeightFraction": 0.4},
            {"EntryId": 2, "WeightFraction": 0.6},
        ]
        self.assertEqual(
            graph_repo.update_weights_batch(self.graph, changes),
            sql_repo.update_weights_batch(self.sql, changes),
        )

    def test_missing_batch_id_rolls_back_prior_candidate_changes(self):
        self.partial()
        self.assert_unchanged(
            graph_repo.NotFoundError,
            lambda: graph_repo.update_weights_batch(
                self.graph,
                [
                    {"EntryId": 1, "WeightFraction": 0.2},
                    {"EntryId": 999, "WeightFraction": 0.1},
                ],
            ),
        )

    def test_delete_complete_rejected_partial_allowed_final_entry_rejected(self):
        self.assert_unchanged(
            graph_repo.BusinessRuleError, lambda: graph_repo.delete_entry(self.graph, 1)
        )
        self.partial()
        self.assertEqual(graph_repo.delete_entry(self.graph, 1)["DeletedEntryId"], 1)
        self.assert_unchanged(
            graph_repo.BusinessRuleError, lambda: graph_repo.delete_entry(self.graph, 2)
        )

    def test_shared_validator_is_called_and_can_prevent_commit(self):
        seen = []

        def mason_validator(candidate):
            seen.append(len(list(candidate)))
            raise ModelIntegrityError("Synthetic shared validation rejection")

        self.graph.validator = mason_validator
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.update_weights_batch(
                self.graph,
                [
                    {"EntryId": 1, "WeightFraction": 0.4},
                    {"EntryId": 2, "WeightFraction": 0.6},
                ],
            ),
        )
        self.assertEqual(len(seen), 1)

    def test_unknown_predicate_and_multiple_weight_values_are_rejected(self):
        for q in [
            Quad(
                resource("AllocationEntry", 1),
                NamedNode(NS + "unexpected"),
                Literal("x"),
                DATA_GRAPH,
            ),
            Quad(
                resource("AllocationEntry", 1),
                NamedNode(NS + "weightFraction"),
                Literal(0.2),
                DATA_GRAPH,
            ),
        ]:
            self.assert_unchanged(
                ModelIntegrityError, lambda q=q: self.graph.mutate(lambda c: c.add(q))
            )

    def test_application_cannot_modify_ontology_or_other_graphs(self):
        q = Quad(
            NamedNode(NS + "test"),
            RDF_TYPE,
            NamedNode(NS + "Class"),
            NamedNode(NS + "ontologyGraph"),
        )
        self.assert_unchanged(
            ModelIntegrityError, lambda: self.graph.mutate(lambda c: c.add(q))
        )

    def test_identifier_required_before_commit(self):
        self.assert_unchanged(
            ModelIntegrityError,
            lambda: self.graph.mutate(
                lambda c: c.update(
                    f"DELETE WHERE {{ GRAPH {DATA_GRAPH} {{ {resource('ETFIdentifier', 1)} ?p ?o }} }}"
                )
            ),
        )

    def test_user_text_cannot_inject_sparql(self):
        attack = 'EXA" } } ; CLEAR ALL; #'
        before = self.graph.snapshot()
        self.assertEqual(graph_repo.search_disclosures(self.graph, ticker=attack), [])
        self.assertEqual(self.graph.snapshot(), before)

    def test_concurrent_batches_publish_valid_coherent_states(self):
        batches = [
            [{"EntryId": 1, "WeightFraction": a}, {"EntryId": 2, "WeightFraction": b}]
            for a, b in [(0.2, 0.8), (0.4, 0.6)]
        ]
        with ThreadPoolExecutor(max_workers=2) as workers:
            list(
                workers.map(
                    lambda batch: graph_repo.update_weights_batch(self.graph, batch),
                    batches,
                )
            )
        result = {
            r["EntryId"]: r["WeightFraction"]
            for r in graph_repo.get_allocation_entries(self.graph, 1)
        }
        self.assertIn((result[1], result[2]), [(0.2, 0.8), (0.4, 0.6)])

    def test_persisted_store_reopens_without_sql_database(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "graph"
            first = GraphDatabase(path, capture_root=ROOT)
            first.load_data(export_connection(self.sql))
            first.flush()
            expected = first.snapshot()
            del first
            gc.collect()
            second = GraphDatabase(path, capture_root=ROOT)
            self.assertEqual(second.snapshot(), expected)
            self.assertEqual(len(graph_repo.search_disclosures(second)), 2)
            del second
            gc.collect()

    def test_ambiguous_dates_require_explicit_date(self):
        self.sql.execute("INSERT INTO Holding VALUES (2,1,1,.2,'2026-11-02')")
        graph = GraphDatabase()
        graph.load_data(export_connection(self.sql))
        with self.assertRaises(graph_repo.ValidationError):
            graph_repo.get_customer_portfolio(graph, "DEMO-C1")
        view = graph_repo.get_customer_portfolio(
            graph, "DEMO-C1", portfolio_id=1, holding_as_of_date="2026-11-01"
        )
        self.assertEqual([h["HoldingId"] for h in view["Holdings"]], [1])

    def test_shared_validator_cannot_return_false_or_modify_candidate(self):
        self.graph.validator = lambda candidate: False
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.create_disclosure(self.graph, self.payload()),
        )

        def mutating_validator(candidate):
            candidate.add(
                Quad(
                    resource("ETF", 1),
                    NamedNode(NS + "unexpected"),
                    Literal("x"),
                    DATA_GRAPH,
                )
            )

        self.graph.validator = mutating_validator
        self.assert_unchanged(
            graph_repo.BusinessRuleError,
            lambda: graph_repo.create_disclosure(self.graph, self.payload()),
        )

    def test_timezone_unknown_capture_is_rejected(self):
        def operation(candidate):
            q = next(
                candidate.quads_for_pattern(
                    resource("SourceDocument", 1),
                    NamedNode(NS + "retrievedAt"),
                    None,
                    DATA_GRAPH,
                )
            )
            candidate.remove(q)
            candidate.add(
                Quad(
                    q.subject,
                    q.predicate,
                    Literal(
                        "2026-11-01T00:00:00",
                        datatype=NamedNode("http://www.w3.org/2001/XMLSchema#dateTime"),
                    ),
                    DATA_GRAPH,
                )
            )

        self.assert_unchanged(ModelIntegrityError, lambda: self.graph.mutate(operation))

    def test_ontology_setup_replaces_only_tbox_including_restriction_blank_nodes(self):
        before = self.graph.snapshot()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.owl"
            path.write_text("""<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
              xmlns:owl="http://www.w3.org/2002/07/owl#" xmlns:rdfs="http://www.w3.org/2000/01/rdf-schema#">
              <owl:Class rdf:about="urn:First"><rdfs:subClassOf><owl:Restriction>
              <owl:onProperty rdf:resource="urn:p"/><owl:cardinality rdf:datatype="http://www.w3.org/2001/XMLSchema#nonNegativeInteger">1</owl:cardinality>
              </owl:Restriction></rdfs:subClassOf></owl:Class></rdf:RDF>""")
            self.graph.load_ontology(path)
            self.assertTrue(
                any(q.subject == NamedNode("urn:First") for q in self.graph.snapshot())
            )
            path.write_text(
                """<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" xmlns:owl="http://www.w3.org/2002/07/owl#"><owl:Class rdf:about="urn:Second"/></rdf:RDF>"""
            )
            self.graph.load_ontology(path)
            self.assertFalse(
                any(q.subject == NamedNode("urn:First") for q in self.graph.snapshot())
            )
            self.assertEqual(
                frozenset(
                    q for q in self.graph.snapshot() if q.graph_name == DATA_GRAPH
                ),
                before,
            )


if __name__ == "__main__":
    unittest.main()
