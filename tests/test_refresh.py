"""Regression coverage for failed, partial, empty and stale official refreshes."""
import datetime as dt
import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import update

NOW = dt.datetime(2026, 10, 22, 9, tzinfo=dt.timezone.utc)
START = '2026-10-23T20:00:00Z'


def payload():
    return json.dumps({'dates': [{'games': [dict(gamePk=7, gameDate=START,
        teams={'away': {'team': {'name': 'Away'}}, 'home': {'team': {'name': 'Home'}}},
        status={'detailedState': 'Scheduled'})]}]}).encode()


def previous():
    row = update.row('Baseball', 'MLB', 7, 'Away', 'Home', START, 'Scheduled', 'https://statsapi.mlb.com')
    return {'generated': '2026-10-22T06:00:00Z', 'matches': [row], 'coverage': [
        {'sport': 'Baseball', 'league': 'MLB', 'status': 'Fetched official MLB schedule', 'source': row['source']} ]}


class Refresh(unittest.TestCase):
    def only_mlb(self):
        return patch.dict(update.SOURCES, {'Baseball': ('MLB', 'https://statsapi.mlb.com/test')}, clear=True)

    def test_failed_fetch_is_not_rebranded_as_fresh(self):
        def fail(_):
            raise OSError('network unavailable')
        with self.only_mlb():
            result = update.refresh(previous(), NOW, fail)
        self.assertEqual(result['matches'], [])
        cached = result['cached_matches'][0]
        self.assertEqual(cached['verified_at'], '2026-10-22T06:00:00Z')
        self.assertIsNone(cached['evidence_sha256'])
        self.assertEqual(cached['freshness'], 'cached')
        self.assertEqual(result['coverage'][0]['state'], 'error')
        self.assertIn('network unavailable', result['coverage'][0]['status'])
        self.assertNotEqual(cached['verified_at'], result['generated'])

    def test_empty_success_clears_old_league(self):
        with self.only_mlb():
            result = update.refresh(previous(), NOW, lambda _: b'{"dates": []}')
        self.assertEqual(result['matches'], [])
        self.assertEqual(result['cached_matches'], [])
        self.assertEqual(result['coverage'][0]['state'], 'ok')
        self.assertEqual(result['coverage'][0]['count'], 0)

    def test_success_records_payload_hash_and_time(self):
        with self.only_mlb():
            result = update.refresh(previous(), NOW, lambda _: payload())
        r = result['matches'][0]
        self.assertEqual(r['verified_at'], NOW.isoformat())
        self.assertEqual(r['evidence_sha256'], hashlib.sha256(payload()).hexdigest())
        self.assertEqual(result['cached_matches'], [])

    def test_partial_failure_does_not_drop_other_league_cache(self):
        old = previous()
        old['matches'].append(update.row('Basketball', 'NBA', 8, 'A', 'B', START, '1', 'https://cdn.nba.com'))
        def fetch(url):
            if 'mlb' in url:
                return payload()
            raise OSError('NBA failed')
        with patch.dict(update.SOURCES, {'Baseball': ('MLB', 'https://statsapi.mlb.com'),
                                         'Basketball': ('NBA', 'https://cdn.nba.com')}, clear=True):
            result = update.refresh(old, NOW, fetch)
        self.assertEqual([r['league'] for r in result['matches']], ['MLB'])
        self.assertEqual([r['league'] for r in result['cached_matches']], ['NBA'])

    def test_expired_and_out_of_window_cache_is_dropped(self):
        old = previous()
        old['matches'][0]['start'] = '2026-10-21T00:00:00Z'
        with self.only_mlb():
            result = update.refresh(old, NOW, lambda _: b'not json')
        self.assertEqual(result['cached_matches'], [])
        self.assertEqual(result['coverage'][0]['state'], 'error')

    def test_repeated_failure_preserves_original_age(self):
        def fail(_):
            raise OSError('offline')
        with self.only_mlb():
            first = update.refresh(previous(), NOW, fail)
            second = update.refresh(first, NOW + dt.timedelta(hours=1), fail)
        self.assertEqual(second['cached_matches'][0]['verified_at'], '2026-10-22T06:00:00Z')
        self.assertEqual(second['coverage'][0]['last_success_at'], '2026-10-22T06:00:00Z')

    def test_invalid_schema_cannot_partially_verify_a_league(self):
        with self.only_mlb():
            result = update.refresh(previous(), NOW, lambda _: b'{"datez": []}')
        self.assertEqual(result['matches'], [])
        self.assertEqual(result['coverage'][0]['state'], 'error')

    def test_naive_date_is_rejected(self):
        for date in ['2026-10-23', '2026-10-23T20:00:00']:
            with self.subTest(date=date), self.assertRaises(ValueError):
                update.row('Baseball', 'MLB', 1, 'A', 'B', date, 'Scheduled', 'https://statsapi.mlb.com')

    def test_unknown_parser_fails_closed(self):
        with self.assertRaises(ValueError):
            update.parse('Tennis', 'ATP', {}, 'https://www.atptour.com')
