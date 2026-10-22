"""Publication cannot infer a timezone, exact start, result, source freshness or edge."""
import datetime as dt
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import board_dates as bd
import release

UTC = dt.timezone.utc
NOW = dt.datetime(2026, 10, 22, 12, tzinfo=UTC)


def record(**overrides):
    r = dict(kind='exact', date='2026-10-22', time='19:30', timezone='CEST',
             source='https://www.euroleaguebasketball.net/en/euroleague/',
             quote='October 22, 2026: Match (19:30 CEST)', checked_at='2026-10-22T10:00:00Z')
    return dict(r, **overrides)


class Release(unittest.TestCase):
    def assess(self, r, now=NOW):
        return release.assess('42', now=now, records={'42': r})

    def test_explicit_official_clock_converts(self):
        result = self.assess(record())
        self.assertEqual(result['start_utc'], '2026-10-22T17:30:00Z')
        self.assertTrue(result['eligible'])
        self.assertEqual(result['expires_at'], result['start_utc'])

    def test_start_boundary_is_not_a_prematch_release(self):
        result = self.assess(record(), dt.datetime(2026, 10, 22, 17, 30, tzinfo=UTC))
        self.assertFalse(result['eligible'])
        self.assertEqual(result['status'], 'start_window_reached')
        self.assertNotIn('final', result['status'])

    def test_no_new_source_check_means_stale_after_24h(self):
        result = self.assess(record(date='2026-10-25'), dt.datetime(2026, 10, 23, 10, tzinfo=UTC))
        self.assertEqual(result['status'], 'stale_source')
        self.assertFalse(result['eligible'])

    def test_et_respects_winter_dst_not_global_utc_minus_four(self):
        result = self.assess(record(date='2026-12-15', time='20:00', timezone='ET'))
        self.assertEqual(result['start_utc'], '2026-12-16T01:00:00Z')

    def test_date_only_and_unknown_zone_stay_blank(self):
        for r in [record(timezone=None), record(kind='date_only'), record(kind='not_before'),
                  record(timezone='track time'), record(timezone='venue local')]:
            with self.subTest(record=r):
                result = self.assess(r)
                self.assertFalse(result['eligible'])
                self.assertIsNone(result['start_utc'])

    def test_official_disagreement_holds_selection(self):
        result = self.assess(record(hold='Conflicting official facts; not resolved by inference'))
        self.assertEqual(result['status'], 'source_conflict')
        self.assertFalse(result['eligible'])

    def test_source_url_alone_cannot_verify(self):
        result = self.assess(record(quote=''))
        self.assertFalse(result['eligible'])
        self.assertIsNone(result['start_utc'])

    def test_invalid_and_future_check_times_fail_closed(self):
        for value in ['2026-10-22T10:00:00', 'garbage', '2026-10-22T13:00:00Z']:
            with self.subTest(value=value):
                self.assertFalse(self.assess(record(checked_at=value))['eligible'])

    def test_archive_build_reproduces_explicit_clock(self):
        with patch.dict(os.environ, {'OLBG_NOW_UTC': '2026-10-22T12:00Z'}):
            self.assertEqual(bd.snapshot_utc(), NOW)
        with patch.dict(os.environ, {}, clear=True):
            # Default must be the committed observation clock, so a CI rebuild of the
            # committed data is byte-identical; freshness is enforced by AS_OF,
            # the 24-hour release window and the in-browser expiry check.
            stored = bd.snapshot_utc()
            self.assertIsNotNone(stored.tzinfo)

    def test_unverified_source_never_becomes_upcoming_by_date(self):
        result = release.assess('missing', '2026-10-30', NOW, {})
        self.assertFalse(result['eligible'])
        self.assertIsNone(result['checked_at'])
        self.assertIsNone(result['start_utc'])


class EvidenceBoundary(unittest.TestCase):
    def assess(self, r):
        return release.assess('42', now=NOW, records={'42': r})

    def test_untrusted_urls_fail_closed(self):
        for url in [None, '', 'not a URL', 'http://www.mlb.com/schedule',
                    'https://www.mlb.com.evil.test/schedule',
                    'https://evil.test/www.mlb.com', 'https://www.mlb.com@evil.test/',
                    'https://user:secret@www.mlb.com/', 'https://www.mlb.com:8443/',
                    'https://www.mlb.com:invalid/', 'https://www.mlb.com/ bad',
                    'https://www.mlb.com/\n', 42]:
            with self.subTest(url=url):
                result = self.assess(record(source=url))
                self.assertFalse(result['eligible'])
                self.assertIsNone(result['start_utc'])
                self.assertIsNone(result['expires_at'])

    def test_allowlist_is_not_a_suffix_match(self):
        self.assertTrue(release.official_clock_url('https://www.mlb.com:443/schedule'))
        self.assertFalse(release.official_clock_url('https://fake.www.mlb.com/'))

    def test_blank_or_nontext_quotes_fail_closed(self):
        for quote in [' ', '\n\t', None, 42, ['a quote']]:
            with self.subTest(quote=quote):
                self.assertFalse(self.assess(record(quote=quote))['eligible'])

    def test_embedded_offset_cannot_be_overwritten(self):
        for clock in ['19:30+05:00', '19:30Z', '19:30:00', '7:30', '25:30']:
            with self.subTest(clock=clock):
                result = self.assess(record(time=clock))
                self.assertFalse(result['eligible'])
                self.assertIsNone(result['start_utc'])
