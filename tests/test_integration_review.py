"""Regression checks from the 3 November schema/application integration review.

Fixtures are fictional. These checks do not verify provider observations or UI.
"""
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))

import quickstart
from dal import repositories as repo, run_analysis_queries as analysis
from test_relational_schema import SCHEMA, fixture


class IntegrationReviewTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA.read_text())
        fixture(self.db)

    def tearDown(self):
        self.db.close()

    def test_missing_batch_entry_rolls_back_valid_changes(self):
        self.db.execute("UPDATE AllocationSnapshot SET CoverageStatus='Partial' WHERE Id=1")
        with self.assertRaises(repo.NotFoundError):
            repo.update_weights_batch(self.db, [
                {'EntryId': 1, 'WeightFraction': .2},
                {'EntryId': 999, 'WeightFraction': .1},
            ])
        self.assertEqual(self.db.execute('SELECT WeightFraction FROM AllocationEntry WHERE Id=1').fetchone()[0], .3)

    def test_coherent_batch_preserves_complete_total(self):
        rows = repo.update_weights_batch(self.db, [
            {'EntryId': 1, 'WeightFraction': .4},
            {'EntryId': 2, 'WeightFraction': .6},
        ])
        self.assertEqual([r['WeightFraction'] for r in rows], [.4, .6])

    def test_disclosure_returns_classification_and_capture_identity(self):
        self.db.execute("INSERT INTO ETFProvider VALUES (2,'Example Publisher','DEMO-R2','SYNTHETIC-REGISTRY',NULL)")
        self.db.execute('UPDATE SourceDocument SET ETFProviderId=2 WHERE Id=1')
        detail = repo.get_disclosure_detail(self.db, 1)
        self.assertEqual(detail['SourceDocumentId'], 1)
        self.assertEqual(detail['PublisherName'], 'Example Publisher')
        self.assertIsNone(detail['PublishedAt'])
        entry = detail['Entries'][0]
        self.assertEqual(entry['SchemeAuthority'], 'Synthetic Authority')
        self.assertEqual(entry['SchemeName'], 'Synthetic Sector')
        self.assertEqual(entry['Version'], 'v1')

    def test_search_filters_exact_etf_and_dimension(self):
        rows = repo.search_disclosures(self.db, etf_id=1, allocation_dimension_id=2)
        self.assertEqual([r['SnapshotId'] for r in rows], [2])
        self.assertEqual(rows[0]['SourceDocumentId'], 1)
        self.assertEqual(rows[0]['ExchangeContext'], 'XTSX')
        self.assertEqual(repo.search_disclosures(self.db, etf_id=999), [])

    def test_portfolio_rejects_ambiguous_holding_dates(self):
        self.db.execute("INSERT INTO Holding VALUES (2,1,1,.2,'2026-11-02')")
        with self.assertRaises(repo.ValidationError):
            repo.get_customer_portfolio(self.db, 'DEMO-C1')
        view = repo.get_customer_portfolio(self.db, 'DEMO-C1', portfolio_id=1,
                                           holding_as_of_date='2026-11-01')
        self.assertEqual([h['HoldingId'] for h in view['Holdings']], [1])
        self.assertEqual(view['Holdings'][0]['ETFId'], 1)

    def test_portfolio_requires_choice_when_customer_has_multiple(self):
        self.db.execute("INSERT INTO Portfolio VALUES (2,1,'DEMO-P2','Second','CAD')")
        with self.assertRaises(repo.ValidationError):
            repo.get_customer_portfolio(self.db, 'DEMO-C1')
        view = repo.get_customer_portfolio(self.db, 'DEMO-C1', portfolio_id=2,
                                           holding_as_of_date='2026-11-01')
        self.assertEqual(view['Portfolio']['Id'], 2)
        self.assertEqual(view['Holdings'], [])
        with self.assertRaises(repo.NotFoundError):
            repo.get_customer_portfolio(self.db, 'DEMO-C1', portfolio_id=999)

    def test_invalid_complete_edit_rolls_back_and_partial_delete_works(self):
        with self.assertRaises(repo.BusinessRuleError):
            repo.update_entry_weight(self.db, 1, .1)
        self.assertEqual(self.db.execute('SELECT WeightFraction FROM AllocationEntry WHERE Id=1').fetchone()[0], .3)
        self.db.execute("UPDATE AllocationSnapshot SET CoverageStatus='Partial' WHERE Id=1")
        self.assertEqual(repo.delete_entry(self.db, 1)['DeletedEntryId'], 1)
        with self.assertRaises(repo.BusinessRuleError):
            repo.delete_entry(self.db, 2)

    def test_create_disclosure_is_atomic_on_invalid_total(self):
        payload = {'ETFId': 1, 'AllocationDimensionId': 1, 'SourceDocumentId': 1,
                   'AllocationAsOfDate': '2026-11-02', 'BasisNote': 'Synthetic example',
                   'CoverageStatus': 'Complete', 'SourceLocator': 'another-sector-table',
                   'Entries': [{'AllocationCategoryId': 1, 'WeightFraction': .2}]}
        with self.assertRaises(repo.BusinessRuleError):
            repo.create_disclosure(self.db, payload)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM AllocationSnapshot').fetchone()[0], 2)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM AllocationEntry').fetchone()[0], 4)
        payload['CoverageStatus'] = 'Partial'
        created = repo.create_disclosure(self.db, payload)
        self.assertEqual(created['CoverageStatus'], 'Partial')
        self.assertEqual(len(created['Entries']), 1)

    def test_query_demo_matches_quickstart_and_is_valid(self):
        from dal.schema_validation import validate_database
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'demo.sqlite3'
            quickstart.build(target)
            conn = analysis._build_in_memory()
            disk = sqlite3.connect(target)
            try:
                validate_database(conn, capture_root=ROOT)
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM AllocationEntry').fetchone()[0], 17)
                self.assertEqual(conn.execute('PRAGMA foreign_key_check').fetchall(), [])
                self.assertEqual(list(conn.iterdump()), list(disk.iterdump()))
            finally:
                conn.close()
                disk.close()

    def test_quickstart_refuses_overwrite_by_default(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'existing.sqlite3'
            target.write_bytes(b'preserve existing database')
            with self.assertRaises(FileExistsError):
                quickstart.build(target)
            self.assertEqual(target.read_bytes(), b'preserve existing database')

    def test_explicit_reset_preserves_existing_file_if_seed_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / 'existing.sqlite3'
            target.write_bytes(b'preserve existing database')
            with patch.object(quickstart, 'seed', side_effect=RuntimeError('seed failed')):
                with self.assertRaisesRegex(RuntimeError, 'seed failed'):
                    quickstart.build(target, reset=True)
            self.assertEqual(target.read_bytes(), b'preserve existing database')


if __name__ == '__main__':
    unittest.main()
