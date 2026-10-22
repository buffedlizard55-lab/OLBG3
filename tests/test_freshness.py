"""Regression tests: advancing builds must not freeze the expiry clock."""
import datetime as dt
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import board_dates as bd


class Freshness(unittest.TestCase):
    def test_default_clock_is_utc_today(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bd.build_date(), dt.datetime.now(dt.timezone.utc).date())

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

    def test_derived_clock_reads_the_label_as_us_eastern(self):
        # validated against organisers' own start times: 04:00 -> 13:00 Almaty, 08:00 -> 14:00 Lyon,
        # 09:00 -> 13:30-15:00 Brussels, 13:00 -> 19:00 CEST handball
        self.assertEqual(bd.resolve_kickoff_utc('Tomorrow 04:00', dt.date(2026, 10, 21))[0], '2026-10-22T08:00Z')
        self.assertEqual(bd.resolve_kickoff_utc('23 Oct 13:45', dt.date(2026, 10, 21))[0], '2026-10-23T17:45Z')
        self.assertEqual(bd.resolve_kickoff_utc('27 May 2027 06:00', dt.date(2026, 10, 21))[0], '2027-05-27T10:00Z')

    def test_derived_clock_leaves_unreadable_labels_blank(self):
        for label in ['', 'garbage', 'Tomorrow 25:00', '31 Feb 09:00']:
            with self.subTest(label=label):
                self.assertIsNone(bd.resolve_kickoff_utc(label)[0])
                self.assertIsNone(bd.started(label))

    def test_started_is_pure_function_of_the_supplied_clock(self):
        now = dt.datetime(2026, 10, 22, 7, 20, tzinfo=dt.timezone.utc)
        self.assertTrue(bd.started('Tomorrow 01:00', now, dt.date(2026, 10, 21)))
        self.assertFalse(bd.started('Tomorrow 04:00', now, dt.date(2026, 10, 21)))
        self.assertFalse(bd.started('23 Oct 13:45', now, dt.date(2026, 10, 21)))
