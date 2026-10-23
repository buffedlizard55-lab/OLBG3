"""Regression tests: advancing builds must not freeze the expiry clock."""
import datetime as dt
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch, mock_open

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import board_dates as bd


class Freshness(unittest.TestCase):
    def test_snapshot_source_file_is_closed(self):
        source = mock_open(read_data='{"checked_at":"2026-10-22T09:10:00Z","events":{}}')
        with patch.dict(os.environ, {}, clear=True), patch('builtins.open', source):
            self.assertEqual(bd.snapshot_utc().isoformat(), '2026-10-22T09:10:00+00:00')
        source().__exit__.assert_called_once()

    def test_default_date_is_the_publication_clock_not_the_wall_clock(self):
        # FL-131: a wall-clock date made every build after midnight non-reproducible, which broke
        # the deploy for 18 h. The default date must follow the committed observation clock.
        source = mock_open(read_data='{"checked_at":"2026-10-22T09:10:00Z","events":{}}')
        with patch.dict(os.environ, {}, clear=True), patch('builtins.open', source):
            self.assertEqual(bd.build_date(), dt.date(2026, 10, 22))

    def test_snapshot_age_is_measured_not_assumed(self):
        source = mock_open(read_data='{"checked_at":"2026-10-22T09:10:00Z","events":{}}')
        later = dt.datetime(2026, 10, 23, 12, 10, tzinfo=dt.timezone.utc)
        with patch.dict(os.environ, {}, clear=True), patch('builtins.open', source):
            self.assertEqual(bd.snapshot_age_hours(now=later), 27.0)
            earlier = dt.datetime(2026, 10, 22, 8, 0, tzinfo=dt.timezone.utc)
            self.assertEqual(bd.snapshot_age_hours(now=earlier), 0.0)

    def test_explicit_archive_date(self):
        with patch.dict(os.environ, {'OLBG_AS_OF': '2026-10-25'}):
            day = bd.build_date()
        self.assertTrue(bd.expired('2026-10-24', day))
        self.assertFalse(bd.expired('2026-10-25', day))
        self.assertFalse(bd.expired(None, day))

    def test_invalid_override_fails_closed(self):
        for value in ['', 'tomorrow', '2026-02-30', '20261022']:
            with self.subTest(value=value), patch.dict(os.environ, {'OLBG_AS_OF': value}):
                with self.assertRaises(ValueError):
                    bd.build_date()

    def test_invalid_labels_stay_blank(self):
        for label in ['31 Feb 09:00', '29 Feb 2027 09:00', 'Today 25:00', 'Tomorrow 03:60', '23 Oct 24:00']:
            with self.subTest(label=label):
                resolved, reason = bd.resolve_start(label)
                self.assertIsNone(resolved)
                self.assertIn('invalid', reason)

    def test_leap_day_and_year_rollover(self):
        self.assertEqual(bd.resolve_start('29 Feb 2028 09:00')[0], '2028-02-29')
        self.assertEqual(bd.resolve_start('Tomorrow 09:00', dt.date(2026, 12, 31))[0], '2027-01-01')

    def test_bare_olbg_clocks_never_get_a_guessed_timezone(self):
        for label in ['Tomorrow 04:00', '23 Oct 13:45', '27 May 2027 06:00']:
            with self.subTest(label=label):
                clock, reason = bd.resolve_kickoff_utc(label)
                self.assertIsNone(clock)
                self.assertIn('unverified', reason)

    def test_bare_clock_cannot_determine_if_a_match_started(self):
        now = dt.datetime(2026, 10, 22, 7, 20, tzinfo=dt.timezone.utc)
        self.assertIsNone(bd.started('Tomorrow 01:00', now, dt.date(2026, 10, 21)))
        self.assertIsNone(bd.started('Tomorrow 04:00', now, dt.date(2026, 10, 21)))
        self.assertIsNone(bd.started('23 Oct 13:45', now, dt.date(2026, 10, 21)))
