"""Route-level checks for the Flask interface and its business-logic layer.

Each test runs against a temporary copy of the fully synthetic demo database, so
the real database is never touched. These tests exercise the routes through
Flask's test client; they do not drive a browser or verify page appearance.
Run from the repository root: python -m unittest discover -s tests -v
"""
from pathlib import Path
import re
import shutil
import sqlite3
import sys
import tempfile
import unittest

from werkzeug.datastructures import MultiDict

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'src'))
sys.path.insert(0, str(ROOT / 'src' / 'ui'))

import quickstart  # noqa: E402
from app import app  # noqa: E402
from biz import disclosures as biz  # noqa: E402
from dal.repositories import ValidationError  # noqa: E402

SYNTHETIC_NOTE = 'Synthetic test disclosure'


def messages(response):
    found = re.findall(r'class="message [a-z]*">(.*?)</div>', response.get_data(as_text=True), re.S)
    return [re.sub(r'\s+', ' ', m).strip() for m in found]


def dump(path):
    connection = sqlite3.connect(str(path))
    try:
        return '\n'.join(connection.iterdump())
    finally:
        connection.close()


class UiTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.template_db = Path(cls.tmp.name) / 'template.sqlite3'
        quickstart.build(cls.template_db)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def setUp(self):
        self.db_path = Path(self.tmp.name) / f'{self.id().split(".")[-1]}.sqlite3'
        shutil.copy(self.template_db, self.db_path)
        app.config['TESTING'] = True
        app.config['DATABASE'] = self.db_path
        self.client = app.test_client()

    def query(self, sql, params=()):
        connection = sqlite3.connect(str(self.db_path))
        try:
            return connection.execute(sql, params).fetchall()
        finally:
            connection.close()

    def post_follow(self, url, data):
        return self.client.post(url, data=data, follow_redirects=True)

    def new_disclosure(self, categories, weights, **overrides):
        fields = {'etf_id': '2', 'dimension_id': '1', 'source_id': '2',
                  'source_locator': 'sector-table', 'as_of_date': '2026-06-30',
                  'coverage_status': 'Partial', 'basis_note': SYNTHETIC_NOTE}
        fields.update(overrides)
        data = MultiDict(fields)
        for category, weight in zip(categories, weights):
            data.add('category', category)
            data.add('weight', weight)
        return self.client.post('/disclosure/new', data=data, follow_redirects=True)


class SearchTests(UiTestCase):
    def rows(self, url):
        return self.client.get(url).get_data(as_text=True).count('View / Edit')

    def test_lists_all_disclosures(self):
        self.assertEqual(self.rows('/'), 5)

    def test_ticker_is_normalized(self):
        self.assertEqual(self.rows('/?ticker=%20sya%20'), 2)

    def test_dimension_and_date_filters(self):
        self.assertEqual(self.rows('/?dimension=Geography'), 3)
        self.assertEqual(self.rows('/?as_of=2026-06-30'), 2)
        self.assertEqual(self.rows('/?ticker=SYC&dimension=Sector&as_of=2026-06-30'), 1)

    def test_invalid_filters_give_messages_not_errors(self):
        for query, fragment in (('as_of=2026-13-45', 'not a real calendar date'),
                                ('as_of=yesterday', 'YYYY-MM-DD'),
                                ('dimension=Bonds', 'Sector or Geography')):
            response = self.client.get('/?' + query)
            self.assertEqual(response.status_code, 200)
            self.assertIn(fragment, ' '.join(messages(response)))

    def test_synthetic_notice_is_visible(self):
        self.assertIn('Fully synthetic demonstration', self.client.get('/').get_data(as_text=True))


class DetailTests(UiTestCase):
    def test_detail_shows_preserved_information(self):
        page = self.client.get('/disclosure/2').get_data(as_text=True)
        self.assertIn('Disclosure Details for SYA', page)
        for expected in ('2026-05-31', 'Sector', 'Complete', 'Fully synthetic demonstration: all identities',
                         'sector-table', 'https://provider.example.invalid/funds/sya/facts',
                         'data/raw/example_sya_facts_20260716.pdf', '2026-09-23T09:15:00.000000Z',
                         'Unknown (not recorded)', 'Example Standards Body', 'Demo Sector Scheme', 'v1',
                         'Information Technology', '31%'):
            self.assertIn(expected, page)

    def test_unknown_classification_is_stated(self):
        page = self.client.get('/disclosure/1').get_data(as_text=True)
        self.assertIn('Not recorded', page)
        self.assertIn('Disclosure-local label', page)

    def test_malformed_or_missing_ids_do_not_error(self):
        for url in ('/disclosure/abc', '/disclosure/999', '/disclosure/-1', '/disclosure/1.5'):
            response = self.client.get(url, follow_redirects=True)
            self.assertEqual(response.status_code, 200, url)
            self.assertTrue(messages(response), url)

    def test_unknown_page_and_wrong_method_are_handled(self):
        self.assertEqual(self.client.get('/nope', follow_redirects=True).status_code, 200)
        self.assertEqual(self.client.get('/update_weights', follow_redirects=True).status_code, 200)


class CreateTests(UiTestCase):
    def test_create_partial_disclosure(self):
        response = self.new_disclosure(['1', '2', '3'], ['0.4', '0.3', '0.1'])
        self.assertIn('Disclosure created.', messages(response))
        self.assertEqual(self.query('SELECT COUNT(*) FROM AllocationSnapshot')[0][0], 6)
        self.assertEqual(self.query('SELECT COUNT(*) FROM AllocationEntry WHERE AllocationSnapshotId=6')[0][0], 3)

    def test_create_complete_disclosure_with_valid_total(self):
        response = self.new_disclosure(['1', '2', '3', '4', '5'], ['0.2'] * 5,
                                       as_of_date='2026-07-31', coverage_status='Complete')
        self.assertIn('Disclosure created.', messages(response))

    def test_create_geography_with_matching_source_and_locator(self):
        response = self.new_disclosure(['6', '7', '8'], ['0.9', '0.09', '0.01'], etf_id='1',
                                       dimension_id='2', source_id='1', source_locator='geography-table',
                                       as_of_date='2026-06-30', coverage_status='Complete')
        self.assertIn('Disclosure created.', messages(response))

    def test_rejected_creates_leave_database_unchanged(self):
        before = dump(self.db_path)
        cases = [
            (dict(categories=[], weights=[]), 'at least one allocation entry'),
            (dict(categories=['1', '1'], weights=['0.1', '0.1']), 'only once'),
            (dict(categories=['', '1'], weights=['0.2', '0.1']), 'needs a category'),
            (dict(categories=['1'], weights=['']), 'needs a weight'),
            (dict(categories=['1'], weights=['2']), 'between 0 and 1'),
            (dict(categories=['1'], weights=['abc']), 'must be a number'),
            (dict(categories=['1', '2'], weights=['0.5', '0.3'], coverage_status='Complete',
                  as_of_date='2026-07-31'), 'must add up to 1'),
            (dict(categories=['6'], weights=['0.5']), 'selected dimension'),
            (dict(categories=['6', '7', '8'], weights=['0.9', '0.09', '0.01'], etf_id='1', dimension_id='2',
                  source_id='1', source_locator='other-table', coverage_status='Complete'), 'source document and locator'),
            (dict(categories=['1'], weights=['0.5'], as_of_date='2026-02-30'), 'not a real calendar date'),
            (dict(categories=['1'], weights=['0.5'], as_of_date=''), 'As-of date is required'),
            (dict(categories=['1'], weights=['0.5'], source_locator='  '), 'locator is required'),
            (dict(categories=['1'], weights=['0.5'], coverage_status='Maybe'), 'Coverage must be'),
            (dict(categories=['1'], weights=['0.5'], etf_id='abc'), 'ETF is missing or invalid'),
            (dict(categories=['1'], weights=['0.5'], etf_id='99'), 'does not exist'),
        ]
        for kwargs, fragment in cases:
            categories, weights = kwargs.pop('categories'), kwargs.pop('weights')
            response = self.new_disclosure(categories, weights, **kwargs)
            self.assertIn(fragment, ' '.join(messages(response)), fragment)
            self.assertEqual(response.status_code, 422, fragment)
            self.assertEqual(dump(self.db_path), before, fragment)

    def test_duplicate_disclosure_is_rejected(self):
        self.new_disclosure(['1'], ['0.5'])
        before = dump(self.db_path)
        response = self.new_disclosure(['1'], ['0.5'])
        self.assertIn('already exists', ' '.join(messages(response)))
        self.assertEqual(dump(self.db_path), before)

    def test_entered_values_are_preserved_after_failure(self):
        response = self.new_disclosure(['1', '2'], ['0.55', '0.125'], source_locator='my-locator',
                                       basis_note='Typed note', as_of_date='2026-02-30')
        page = response.get_data(as_text=True)
        for kept in ('my-locator', 'Typed note', '2026-02-30', '0.55', '0.125'):
            self.assertIn(kept, page)


class UpdateAndDeleteTests(UiTestCase):
    def batch(self, snapshot_id, pairs):
        data = MultiDict({'snapshot_id': str(snapshot_id)})
        for entry_id, weight in pairs:
            data.add('entry_id', str(entry_id))
            data.add('weight', str(weight))
        return self.client.post('/update_weights', data=data, follow_redirects=True)

    def test_coherent_multi_entry_update_is_saved(self):
        response = self.batch(2, [(4, 0.350), (5, 0.130), (6, 0.105), (7, 0.040), (8, 0.375)])
        self.assertIn('Saved 5 weight(s) together.', messages(response))
        self.assertEqual(self.query('SELECT WeightFraction FROM AllocationEntry WHERE Id=4')[0][0], 0.35)
        self.assertEqual(self.query('SELECT WeightFraction FROM AllocationEntry WHERE Id=8')[0][0], 0.375)

    def test_incoherent_update_is_rejected_and_values_kept(self):
        before = dump(self.db_path)
        response = self.batch(2, [(4, 0.35), (5, 0.130), (6, 0.105), (7, 0.040), (8, 0.415)])
        self.assertEqual(response.status_code, 422)
        self.assertIn('must add up to 1', ' '.join(messages(response)))
        self.assertIn('value="0.35"', response.get_data(as_text=True))
        self.assertEqual(dump(self.db_path), before)

    def test_invalid_updates_leave_database_unchanged(self):
        before = dump(self.db_path)
        cases = [
            ([(4, 'abc')], 'must be a number'),
            ([(4, '')], 'Weight is required'),
            ([(4, 1.5)], 'between 0 and 1'),
            ([(4, -0.1)], 'between 0 and 1'),
            ([(4, 'nan')], 'between 0 and 1'),
            ([('x', 0.3)], 'missing or invalid'),
            ([(999, 0.3)], 'do not belong to this disclosure'),
            ([(4, 0.3), (4, 0.3)], 'submitted twice'),
            ([(1, 0.5)], 'do not belong to this disclosure'),
        ]
        for pairs, fragment in cases:
            response = self.batch(2, pairs)
            self.assertIn(fragment, ' '.join(messages(response)), fragment)
            self.assertNotEqual(response.status_code, 500)
            self.assertEqual(dump(self.db_path), before, fragment)

    def test_missing_or_bad_snapshot_id_is_handled(self):
        for sid in ('', 'abc'):
            response = self.client.post('/update_weights', data={'snapshot_id': sid, 'entry_id': '4', 'weight': '0.3'},
                                        follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn('missing or invalid', ' '.join(messages(response)))

    def test_delete_from_complete_disclosure_is_rejected(self):
        before = dump(self.db_path)
        response = self.post_follow('/delete_entry', {'entry_id': 4, 'snapshot_id': 2})
        self.assertIn('would make the total 0.69', ' '.join(messages(response)))
        self.assertEqual(dump(self.db_path), before)

    def test_delete_in_partial_disclosure_and_last_entry_rule(self):
        self.new_disclosure(['1', '2', '3'], ['0.4', '0.3', '0.1'])
        ids = [r[0] for r in self.query('SELECT Id FROM AllocationEntry WHERE AllocationSnapshotId=6 ORDER BY Id')]
        self.assertIn('Entry deleted.', messages(self.post_follow('/delete_entry', {'entry_id': ids[2], 'snapshot_id': 6})))
        self.assertIn('Entry deleted.', messages(self.post_follow('/delete_entry', {'entry_id': ids[1], 'snapshot_id': 6})))
        before = dump(self.db_path)
        response = self.post_follow('/delete_entry', {'entry_id': ids[0], 'snapshot_id': 6})
        self.assertIn('must keep at least one entry', ' '.join(messages(response)))
        self.assertEqual(dump(self.db_path), before)
        self.assertEqual(self.query('SELECT COUNT(*) FROM AllocationEntry WHERE AllocationSnapshotId=6')[0][0], 1)

    def test_delete_bad_input_is_handled(self):
        before = dump(self.db_path)
        for data, fragment in (({'entry_id': 'abc', 'snapshot_id': 2}, 'missing or invalid'),
                               ({'entry_id': 999, 'snapshot_id': 2}, 'do not belong'),
                               ({'entry_id': 1, 'snapshot_id': 2}, 'do not belong')):
            response = self.post_follow('/delete_entry', data)
            self.assertEqual(response.status_code, 200)
            self.assertIn(fragment, ' '.join(messages(response)))
        self.assertEqual(dump(self.db_path), before)


class PortfolioTests(UiTestCase):
    def test_form_without_customer(self):
        page = self.client.get('/portfolio').get_data(as_text=True)
        self.assertIn('1001 - Alice Chen', page)
        self.assertNotIn('name="holding_date"', page)

    def test_explicit_portfolio_and_date_selection_and_separate_dates(self):
        page = self.client.get('/portfolio?customer=1001').get_data(as_text=True)
        for expected in ('name="portfolio_id"', 'name="holding_date"', 'P-ALICE-01', 'Holding as-of date',
                         '2026-08-01', 'allocation as of 2026-05-31', 'allocation as of 2026-06-30', 'SYA', 'SYC'):
            self.assertIn(expected, page)

    def test_explicit_choices_are_accepted(self):
        page = self.client.get('/portfolio?customer=1002&portfolio_id=2&holding_date=2026-08-01').get_data(as_text=True)
        self.assertIn('Balanced Portfolio', page)
        self.assertIn('0.5', page)

    def test_bad_inputs_are_handled(self):
        for url, fragment in (('/portfolio?customer=9999', 'not found'),
                              ('/portfolio?customer=1001&portfolio_id=2', 'does not belong'),
                              ('/portfolio?customer=1001&holding_date=2026-99-99', 'not a real calendar date')):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertIn(fragment, ' '.join(messages(response)))
        page = self.client.get('/portfolio?customer=1001&holding_date=2020-01-01').get_data(as_text=True)
        self.assertIn('No holdings', page)


class BusinessLogicTests(unittest.TestCase):
    def test_weight_parsing(self):
        self.assertEqual(biz.parse_weight(' 0.5 '), 0.5)
        self.assertEqual(biz.parse_weight('0'), 0.0)
        self.assertEqual(biz.parse_weight('1'), 1.0)
        for bad in (None, '', '  ', 'abc', '1.0001', '-0.001', 'nan', 'inf'):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                biz.parse_weight(bad)

    def test_date_parsing(self):
        self.assertEqual(biz.parse_date('2026-02-28', 'D'), '2026-02-28')
        for bad in ('', '2026-02-30', '20260228', '2026-2-8', 'abc', None):
            with self.assertRaises(ValidationError, msg=repr(bad)):
                biz.parse_date(bad, 'D')

    def test_id_parsing_and_ticker(self):
        self.assertEqual(biz.parse_id(' 7 ', 'X'), 7)
        for bad in (None, '', 'a', '1.5'):
            with self.assertRaises(ValidationError):
                biz.parse_id(bad, 'X')
        self.assertEqual(biz.normalize_ticker(' sya '), 'SYA')
        self.assertIsNone(biz.normalize_ticker('  '))

    def test_percent_format(self):
        self.assertEqual(biz.format_percent(0.31), '31%')
        self.assertEqual(biz.format_percent(0.0125), '1.25%')
        self.assertEqual(biz.format_percent(0.985), '98.5%')


if __name__ == '__main__':
    unittest.main()
