"""Behavioral checks for Taimoor's schema and transaction-level model rules.

All fixtures are explicitly synthetic and are not the team's demonstration data.
Run from the repository root: python -m unittest discover -s tests -v
"""

from pathlib import Path
import sqlite3
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dal.schema_validation import (  # noqa: E402
    ModelIntegrityError, disclosure_context, scheme_context,
    validate_database, validated_transaction,
)

SCHEMA = ROOT / 'src/dal/sql/schema.sql'
RETRIEVED = '2026-11-01T00:00:00.000000Z'
URL = 'https://example.invalid/synthetic-disclosure.txt'


def fixture(connection):
    """One valid state containing records in all twelve model relations."""
    with validated_transaction(connection, capture_root=ROOT):
        connection.execute("INSERT INTO Customer VALUES (1, 'DEMO-C1', 'Example', 'Customer', NULL)")
        connection.execute("INSERT INTO ETFProvider VALUES (1, 'Example Provider Ltd', 'DEMO-R1', 'SYNTHETIC-REGISTRY', NULL)")
        connection.executemany('INSERT INTO AllocationDimension VALUES (?, ?)', [(1, 'Sector'), (2, 'Geography')])
        connection.execute("INSERT INTO ClassificationScheme VALUES (1, 'Synthetic Authority', 'Synthetic Sector', 'v1', NULL)")
        connection.execute("INSERT INTO ClassificationScheme VALUES (2, 'Synthetic Authority', 'Unresolved Scheme', NULL, NULL)")
        connection.execute("INSERT INTO Portfolio VALUES (1, 1, 'DEMO-P1', 'Example Portfolio', 'CAD')")
        connection.execute("INSERT INTO ETF VALUES (1, 1, 'Example ETF A', 'CA', 'CAD', '2020-01-01')")
        connection.execute("INSERT INTO ETFIdentifier VALUES (1, 1, 'Ticker', 'EXA', 'XTSX')")
        connection.execute("INSERT INTO Holding VALUES (1, 1, 1, 0.5, '2026-11-01')")
        connection.execute('INSERT INTO SourceDocument VALUES (1, 1, ?, ?, NULL, ?, ?)',
                           (URL, RETRIEVED, 'tests/fixtures/synthetic_disclosure.txt', 'Synthetic fixture'))
        sector = scheme_context('Synthetic Authority', 'Synthetic Sector', 'v1')
        geography = disclosure_context(URL, RETRIEVED, 'geography-table', 'Geography')
        connection.executemany('INSERT INTO AllocationCategory VALUES (?, ?, ?, ?, ?, ?)', [
            (1, 1, 1, 'Technology', 'TECH', sector),
            (2, 1, 1, 'Other', None, sector),
            (3, 2, None, 'Canada', 'CA', geography),
            (4, 2, None, 'Other', None, geography),
        ])
        connection.executemany('INSERT INTO AllocationSnapshot VALUES (?, 1, ?, 1, ?, ?, ?, ?)', [
            (1, 1, '2026-10-31', 'Synthetic test weights', 'Complete', 'sector-table'),
            (2, 2, '2026-10-31', 'Synthetic test weights', 'Complete', 'geography-table'),
        ])
        connection.executemany('INSERT INTO AllocationEntry VALUES (?, ?, ?, ?)', [
            (1, 1, 1, .3), (2, 1, 2, .7), (3, 2, 3, .6), (4, 2, 4, .4),
        ])


class RelationalSchemaTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:', isolation_level=None)
        self.db.executescript(SCHEMA.read_text())
        fixture(self.db)

    def tearDown(self):
        self.db.close()

    def test_fresh_schema_valid_state_and_generated_id(self):
        validate_database(self.db, capture_root=ROOT)
        self.assertEqual(self.db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        cursor = self.db.execute("INSERT INTO Customer (CustomerNumber, GivenName, FamilyName) VALUES ('DEMO-C2', 'Another', 'Person')")
        self.assertIsInstance(cursor.lastrowid, int)
        self.assertEqual(self.db.execute('PRAGMA foreign_key_check').fetchall(), [])

    def test_customer_business_key_and_nonunique_email(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Customer VALUES (2, 'DEMO-C1', 'Other', 'Person', NULL)")
        self.db.execute("UPDATE Customer SET Email = 'shared@example.invalid' WHERE Id = 1")
        self.db.execute("INSERT INTO Customer VALUES (2, 'DEMO-C2', 'Other', 'Person', 'shared@example.invalid')")

    def test_provider_registration_is_scoped_to_registry(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO ETFProvider VALUES (2, 'Another name', 'DEMO-R1', 'SYNTHETIC-REGISTRY', NULL)")
        self.db.execute("INSERT INTO ETFProvider VALUES (2, 'Example Provider Ltd', 'DEMO-R1', 'OTHER-SYNTHETIC-REGISTRY', NULL)")

    def test_portfolio_reference_is_scoped_to_owner(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Portfolio VALUES (2, 1, 'DEMO-P1', 'Duplicate', 'CAD')")
        self.db.execute("INSERT INTO Customer VALUES (2, 'DEMO-C2', 'Other', 'Person', NULL)")
        self.db.execute("INSERT INTO Portfolio VALUES (2, 2, 'DEMO-P1', 'Same reference, different owner', 'CAD')")

    def test_duplicate_holding_date_rejected_but_new_date_allowed(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Holding VALUES (2, 1, 1, .2, '2026-11-01')")
        self.db.execute("INSERT INTO Holding VALUES (2, 1, 1, .2, '2026-11-02')")

    def test_isin_duplicate_with_null_exchange_is_rejected(self):
        self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 1, 'ISIN', 'CA0000000001', NULL)")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO ETFIdentifier VALUES (3, 1, 'ISIN', 'CA0000000001', NULL)")

    def test_ticker_requires_exchange_and_is_unique_within_it(self):
        for exchange in [None, '', '  ']:
            with self.subTest(exchange=exchange), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 1, 'Ticker', 'EXB', ?)", (exchange,))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 1, 'Ticker', 'EXA', 'XTSX')")
        self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 1, 'Ticker', 'EXA', 'XNYS')")

    def test_isin_context_and_format(self):
        for value, exchange in [('TOOSHORT', None), ('CA0000000001', 'XTSX'), ('CA000000000A', None)]:
            with self.subTest(value=value, exchange=exchange), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 1, 'ISIN', ?, ?)", (value, exchange))

    def test_known_version_unique_unknown_versions_remain_unresolved(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO ClassificationScheme VALUES (3, 'Synthetic Authority', 'Synthetic Sector', 'v1', NULL)")
        self.db.execute("INSERT INTO ClassificationScheme VALUES (3, 'Synthetic Authority', 'Unresolved Scheme', NULL, NULL)")
        validate_database(self.db)

    def test_category_labels_are_unique_only_inside_context_and_dimension(self):
        context = self.db.execute('SELECT ContextKey FROM AllocationCategory WHERE Id = 1').fetchone()[0]
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO AllocationCategory VALUES (5, 1, 1, 'Technology', NULL, ?)", (context,))
        self.db.execute("INSERT INTO AllocationCategory VALUES (5, 1, NULL, 'Technology', NULL, 'source:another-context')")

    def test_disclosure_capture_and_block_uniqueness(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO SourceDocument VALUES (2, 1, ?, ?, NULL, ?, NULL)',
                            (URL, RETRIEVED, 'tests/fixtures/synthetic_disclosure.txt'))
        self.db.execute('INSERT INTO SourceDocument VALUES (2, 1, ?, ?, NULL, ?, NULL)',
                        (URL, '2026-11-02T00:00:00.000000Z', 'tests/fixtures/synthetic_disclosure.txt'))
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO AllocationSnapshot VALUES (3, 1, 1, 1, '2026-10-31', 'Other wording', 'Complete', 'sector-table')")

    def test_duplicate_snapshot_category_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('INSERT INTO AllocationEntry VALUES (5, 1, 1, .1)')

    def test_fraction_bounds_and_strict_numeric_type(self):
        for table, id in [('Holding', 1), ('AllocationEntry', 1)]:
            for weight in [-.01, 1.01, 30, 'not-a-number', None, float('inf')]:
                with self.subTest(table=table, weight=weight), self.assertRaises(sqlite3.IntegrityError):
                    self.db.execute(f'UPDATE {table} SET WeightFraction = ? WHERE Id = ?', (weight, id))

    def test_calendar_dates_and_canonical_timestamps(self):
        for value in ['2026-02-30', '2026-13-01', '2026-1-01', 'invalid']:
            with self.subTest(value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute('UPDATE Holding SET HoldingAsOfDate = ? WHERE Id = 1', (value,))
        for value in ['2026-02-30T00:00:00.000000Z', '2026-11-01T25:00:00.000000Z',
                      '2026-11-01T00:00:00Z', '2026-11-01T00:00:00.12345xZ', 'invalid']:
            with self.subTest(value=value), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute('UPDATE SourceDocument SET RetrievedAt = ? WHERE Id = 1', (value,))

    def test_required_values_domains_and_format(self):
        statements = [
            "UPDATE Customer SET CustomerNumber = ' ' WHERE Id = 1",
            "UPDATE Customer SET GivenName = NULL WHERE Id = 1",
            "UPDATE AllocationDimension SET DimensionName = 'Other' WHERE Id = 1",
            "UPDATE AllocationSnapshot SET CoverageStatus = 'Maybe' WHERE Id = 1",
            "UPDATE ETF SET BaseCurrency = 'cad' WHERE Id = 1",
            "UPDATE ETF SET DomicileCountryCode = 'Canada' WHERE Id = 1",
        ]
        for sql in statements:
            with self.subTest(sql=sql), self.assertRaises(sqlite3.IntegrityError):
                self.db.execute(sql)

    def test_missing_parent_and_referenced_parent_delete_are_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute("INSERT INTO Portfolio VALUES (2, 999, 'X', 'Missing parent', 'CAD')")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.execute('DELETE FROM ETF WHERE Id = 1')

    def test_cross_dimension_entry_insert_and_update_are_rejected(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'dimensions must agree'):
            self.db.execute('INSERT INTO AllocationEntry VALUES (5, 1, 3, .1)')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'dimensions must agree'):
            self.db.execute('UPDATE AllocationEntry SET AllocationCategoryId = 3 WHERE Id = 1')

    def test_later_parent_dimension_changes_cannot_break_entries(self):
        for table in ['AllocationSnapshot', 'AllocationCategory']:
            with self.subTest(table=table), self.assertRaisesRegex(sqlite3.IntegrityError, 'dimension conflicts'):
                self.db.execute(f'UPDATE {table} SET AllocationDimensionId = 2 WHERE Id = 1')

    def test_empty_snapshot_write_rolls_back(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'at least one entry'):
            with validated_transaction(self.db):
                self.db.execute("INSERT INTO AllocationSnapshot VALUES (3, 1, 1, 1, '2026-11-01', 'Test', 'Partial', 'new-table')")
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM AllocationSnapshot WHERE Id = 3').fetchone()[0], 0)

    def test_deleting_final_entries_rolls_back_whole_transaction(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'at least one entry'):
            with validated_transaction(self.db):
                self.db.execute('DELETE FROM AllocationEntry WHERE AllocationSnapshotId = 1')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM AllocationEntry WHERE AllocationSnapshotId = 1').fetchone()[0], 2)

    def test_etf_without_identifier_rolls_back(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'at least one identifier'):
            with validated_transaction(self.db):
                self.db.execute("INSERT INTO ETF VALUES (2, 1, 'Example B', 'CA', 'CAD', NULL)")
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM ETF WHERE Id = 2').fetchone()[0], 0)

    def test_parent_and_child_can_be_created_atomically(self):
        with validated_transaction(self.db):
            self.db.execute("INSERT INTO ETF VALUES (2, 1, 'Example B', 'CA', 'CAD', NULL)")
            self.db.execute("INSERT INTO ETFIdentifier VALUES (2, 2, 'Ticker', 'EXB', 'XTSX')")
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM ETF WHERE Id = 2').fetchone()[0], 1)

    def test_complete_totals_checked_and_updates_roll_back(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'complete total'):
            with validated_transaction(self.db):
                self.db.execute('UPDATE AllocationEntry SET WeightFraction = .5 WHERE Id = 1')
        self.assertEqual(self.db.execute('SELECT WeightFraction FROM AllocationEntry WHERE Id = 1').fetchone()[0], .3)

    def test_partial_and_unknown_totals_need_not_equal_one(self):
        for status in ['Partial', 'Unknown']:
            with validated_transaction(self.db):
                self.db.execute('UPDATE AllocationSnapshot SET CoverageStatus = ? WHERE Id = 1', (status,))
                self.db.execute('UPDATE AllocationEntry SET WeightFraction = .1 WHERE Id = 1')

    def test_rounding_tolerance_boundary_and_configurable_value(self):
        with validated_transaction(self.db):
            self.db.execute('UPDATE AllocationEntry SET WeightFraction = .305 WHERE Id = 1')
        with self.assertRaises(ModelIntegrityError):
            with validated_transaction(self.db):
                self.db.execute('UPDATE AllocationEntry SET WeightFraction = .3051 WHERE Id = 1')
        with self.assertRaises(ModelIntegrityError):
            validate_database(self.db, total_tolerance=.001)
        for tolerance in [-1, 1, float('nan'), float('inf')]:
            with self.subTest(tolerance=tolerance), self.assertRaises(ValueError):
                validate_database(self.db, total_tolerance=tolerance)

    def test_unknown_context_cannot_be_reused_in_another_capture(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'ContextKey'):
            with validated_transaction(self.db):
                self.db.execute('INSERT INTO SourceDocument VALUES (2, 1, ?, ?, NULL, ?, NULL)',
                                (URL, '2026-11-02T00:00:00.000000Z', 'tests/fixtures/synthetic_disclosure.txt'))
                self.db.execute("INSERT INTO AllocationSnapshot VALUES (3, 1, 2, 2, '2026-10-31', 'Test', 'Partial', 'geography-table')")
                self.db.execute('INSERT INTO AllocationEntry VALUES (5, 3, 3, .6)')
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM SourceDocument').fetchone()[0], 1)

    def test_unknown_version_also_requires_disclosure_local_context(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'ContextKey'):
            with validated_transaction(self.db):
                self.db.execute('UPDATE AllocationCategory SET ClassificationSchemeId = 2 WHERE Id = 1')

    def test_known_scheme_context_can_be_reused_across_captures(self):
        with validated_transaction(self.db):
            self.db.execute('INSERT INTO SourceDocument VALUES (2, 1, ?, ?, NULL, ?, NULL)',
                            (URL, '2026-11-02T00:00:00.000000Z', 'tests/fixtures/synthetic_disclosure.txt'))
            self.db.execute("INSERT INTO AllocationSnapshot VALUES (3, 1, 1, 2, '2026-10-31', 'Test', 'Partial', 'sector-table')")
            self.db.execute('INSERT INTO AllocationEntry VALUES (5, 3, 1, .3)')

    def test_editing_scheme_version_requires_matching_context_update(self):
        with self.assertRaisesRegex(ModelIntegrityError, 'ContextKey'):
            with validated_transaction(self.db):
                self.db.execute("UPDATE ClassificationScheme SET Version = 'v2' WHERE Id = 1")
        self.assertEqual(self.db.execute('SELECT Version FROM ClassificationScheme WHERE Id = 1').fetchone()[0], 'v1')

    def test_capture_reference_must_exist_inside_project_when_checked(self):
        for reference in ['missing-capture.txt', '../outside.txt']:
            with self.subTest(reference=reference), self.assertRaisesRegex(ModelIntegrityError, 'retained capture'):
                with validated_transaction(self.db, capture_root=ROOT):
                    self.db.execute('UPDATE SourceDocument SET CapturedFileRef = ? WHERE Id = 1', (reference,))

    def test_foreign_keys_must_be_enabled_before_application_transaction(self):
        self.db.execute('PRAGMA foreign_keys = OFF')
        with self.assertRaisesRegex(ModelIntegrityError, 'foreign keys'):
            with validated_transaction(self.db):
                pass

    def test_nested_transaction_is_not_silently_committed(self):
        self.db.execute('BEGIN')
        with self.assertRaisesRegex(ValueError, 'no active transaction'):
            with validated_transaction(self.db):
                pass
        self.assertTrue(self.db.in_transaction)
        self.db.execute('ROLLBACK')

    def test_external_fk_violation_detected_after_enforcement_restored(self):
        self.db.execute('PRAGMA foreign_keys = OFF')
        self.db.execute("INSERT INTO Portfolio VALUES (2, 999, 'BAD', 'Invalid external import', 'CAD')")
        self.db.execute('PRAGMA foreign_keys = ON')
        with self.assertRaisesRegex(ModelIntegrityError, 'missing parent'):
            validate_database(self.db)


if __name__ == '__main__':
    unittest.main()
