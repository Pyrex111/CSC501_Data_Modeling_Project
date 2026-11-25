"""Milestone 5: every Flask route test rerun against the knowledge graph.

Each test gets a fresh in-memory graph opened through semantic.runtime, the same
startup path the application uses: Mason's ontology is loaded into its own named
graph and both the native graph validator and the M4 parity bridge are attached.
The 356 synthetic ABox triples come from the accepted seed, exactly as in
quickstart_semantic.py. No SQLite file is read by the routes in these tests.

"Unchanged" checks compare the complete set of quads (ontology + data graphs), so
a rejected form submission must leave the whole store identical.
Run from the repository root: python -m unittest discover -s tests -v
"""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'src' / 'ui'))
sys.path.insert(0, str(ROOT / 'tests'))

from app import app  # noqa: E402
from dal.seed_data import seed  # noqa: E402
from semantic import repositories as graph_repositories  # noqa: E402
from semantic.codec import export_connection  # noqa: E402
from semantic.runtime import open_graph_database  # noqa: E402
from semantic.vocabulary import DATA_GRAPH, NS, ROOT as VOCAB_ROOT, schema_connection  # noqa: E402

import test_ui_routes as m4  # noqa: E402

_QUADS = None


def seed_quads():
    """Synthetic ABox quads from the accepted seed, built once per test run."""
    global _QUADS
    if _QUADS is None:
        sql = schema_connection()
        try:
            seed(sql, VOCAB_ROOT)
            _QUADS = list(export_connection(sql))
        finally:
            sql.close()
    return _QUADS


class GraphBackendMixin:
    """Swap the SQLite fixture for a validated in-memory knowledge graph."""

    @classmethod
    def setUpClass(cls):
        seed_quads()

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.graph = open_graph_database(None)  # in-memory store, real startup path
        self.graph.load_data(seed_quads())
        app.config['TESTING'] = True
        app.config['BACKEND'] = 'graph'
        app.config['GRAPH'] = self.graph
        self.client = app.test_client()

    def tearDown(self):
        app.config['GRAPH'] = None
        app.config['BACKEND'] = 'graph'

    def query(self, *args, **kwargs):  # pragma: no cover - guard against SQL use
        raise AssertionError('Graph-backed UI tests must not query SQLite')

    def state(self):
        return self.graph.snapshot()

    def snapshot_count(self):
        return len(graph_repositories.search_disclosures(self.graph))

    def entry_ids(self, snapshot_id):
        return sorted(e['EntryId'] for e in
                      graph_repositories.get_allocation_entries(self.graph, snapshot_id))

    def weight(self, entry_id):
        rows = self.graph.select(
            f'SELECT ?w WHERE {{ GRAPH {DATA_GRAPH} {{ ?e a <{NS}AllocationEntry> ; '
            f'<{NS}recordId> {int(entry_id)} ; <{NS}weightFraction> ?w }} }}')
        self.assertEqual(len(rows), 1)
        return float(rows[0]['w'])


class GraphSearchTests(GraphBackendMixin, m4.SearchTests):
    def test_data_source_label_names_the_graph(self):
        page = self.client.get('/').get_data(as_text=True)
        self.assertIn('Data source: Knowledge graph', page)


class GraphDetailTests(GraphBackendMixin, m4.DetailTests):
    pass


class GraphCreateTests(GraphBackendMixin, m4.CreateTests):
    def test_created_disclosure_is_stored_as_triples(self):
        before = len(self.graph.snapshot())
        self.new_disclosure(['1', '2', '3'], ['0.4', '0.3', '0.1'])
        rows = self.graph.select(
            f'SELECT ?e WHERE {{ GRAPH {DATA_GRAPH} {{ ?s a <{NS}AllocationSnapshot> ; '
            f'<{NS}recordId> 6 . ?e <{NS}inSnapshot> ?s }} }}')
        self.assertEqual(len(rows), 3)
        self.assertGreater(len(self.graph.snapshot()), before)


class GraphUpdateAndDeleteTests(GraphBackendMixin, m4.UpdateAndDeleteTests):
    pass


class GraphPortfolioTests(GraphBackendMixin, m4.PortfolioTests):
    pass


class GraphStartupTests(unittest.TestCase):
    def test_missing_store_gives_clear_message(self):
        app.config['BACKEND'] = 'graph'
        app.config['GRAPH'] = None
        old = app.config['GRAPH_STORE']
        app.config['GRAPH_STORE'] = ROOT / 'data' / 'definitely_missing_store'
        try:
            response = app.test_client().get('/', follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('quickstart_semantic.py', response.get_data(as_text=True))
        finally:
            app.config['GRAPH_STORE'] = old
            app.config['GRAPH'] = None


# Do not run the SQLite classes twice when this module is collected.
del m4

if __name__ == '__main__':
    unittest.main()
