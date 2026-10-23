"""Publication time must advance without pretending source evidence is new."""
import datetime as dt
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import mock_open, patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import board_dates as bd
import publication_clock
import release

UTC = dt.timezone.utc
BEFORE = dt.datetime(2026, 10, 23, 17, 22, tzinfo=UTC)
AFTER = dt.datetime(2026, 10, 23, 19, 20, tzinfo=UTC)
RECORD = dict(kind='exact', date='2026-10-23', time='18:15', timezone='UTC',
              source='https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/',
              quote='Olympiacos vs Paris, October 23, 2026 (20:15 CEST)',
              checked_at='2026-10-23T17:07:00Z')


class PublicationClock(unittest.TestCase):
    def test_clock_writer_writes_only_its_explicit_output(self):
        evidence = (ROOT / 'data/release_checks.json').read_bytes()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'publication.json'
            result = publication_clock.advance(AFTER.replace(second=42), path=path)
            self.assertEqual(result['publication_as_of'], '2026-10-23T19:20:00Z')
            self.assertEqual(json.loads(path.read_text()), result)
            self.assertEqual(sorted(p.name for p in Path(tmp).iterdir()), ['publication.json'])
        self.assertEqual((ROOT / 'data/release_checks.json').read_bytes(), evidence)

    def test_naive_clock_is_rejected(self):
        with self.assertRaises(ValueError):
            publication_clock.advance(dt.datetime(2026, 10, 23, 19, 20))

    def test_publication_can_advance_without_source_refresh(self):
        with patch.dict(os.environ, {}, clear=True), patch('builtins.open', mock_open(
                read_data='{"publication_as_of":"2026-10-23T19:20:00Z"}')):
            self.assertEqual(bd.snapshot_utc(), AFTER)
        old = release.assess('42', now=BEFORE, records={'42': RECORD})
        current = release.assess('42', now=AFTER, records={'42': RECORD})
        self.assertTrue(old['eligible'])
        self.assertFalse(current['eligible'])
        self.assertEqual(current['status'], 'start_window_reached')
        self.assertEqual(current['checked_at'], RECORD['checked_at'])
        self.assertEqual(old['source'], current['source'])

    def test_refresh_is_not_source_retrieval(self):
        with patch.object(bd, 'source_snapshot_utc', return_value=BEFORE), \
                patch.object(bd, 'snapshot_utc', return_value=AFTER), \
                patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bd.snapshot_age_hours(now=AFTER), 2.0)

    def test_missing_or_invalid_publication_clock_fails_closed(self):
        for doc in ['{}', '{"publication_as_of":"2026-10-23T19:20:00"}',
                    '{"publication_as_of":"2026-02-30T19:20:00Z"}',
                    '{"publication_as_of":42}']:
            with self.subTest(doc=doc), patch.dict(os.environ, {}, clear=True), \
                    patch('builtins.open', mock_open(read_data=doc)):
                with self.assertRaises((KeyError, ValueError)):
                    bd.snapshot_utc()
        with patch.dict(os.environ, {}, clear=True), \
                patch('builtins.open', side_effect=FileNotFoundError):
            with self.assertRaises(FileNotFoundError):
                bd.snapshot_utc()

    def test_landing_page_does_not_claim_every_market_is_priced(self):
        template = (ROOT / 'tools/build_site.py').read_text()
        self.assertIn('Not every fixture has a price, handicap or total', template)
        self.assertNotIn('total for every fixture', template)

    def test_checked_in_workflow_advances_clock_before_build(self):
        workflow = (ROOT / '.github/workflows/pages.yml').read_text()
        self.assertLess(workflow.index('python scripts/publication_clock.py'),
                        workflow.index('python scripts/build.py'))


class ReleaseIntegrity(unittest.TestCase):
    def test_stored_eligible_boolean_cannot_reanimate_started_pick(self):
        old = release.assess('42', now=BEFORE, records={'42': RECORD})
        self.assertTrue(release.high_release_errors('42', old, AFTER, {'42': RECORD}))

    def test_current_release_passes(self):
        current = release.assess('42', now=BEFORE, records={'42': RECORD})
        self.assertEqual(release.high_release_errors('42', current, BEFORE, {'42': RECORD}), [])

    def test_missing_or_tampered_release_cannot_publish_high(self):
        current = release.assess('42', now=BEFORE, records={'42': RECORD})
        for value in [None, {}, dict(current, source='https://www.mlb.com/'),
                      dict(current, start_utc='2026-10-24T18:15:00Z'),
                      dict(current, eligible=False)]:
            with self.subTest(value=value):
                self.assertTrue(release.high_release_errors('42', value, BEFORE, {'42': RECORD}))

    def test_future_check_does_not_publish_an_unconfirmed_start(self):
        record = dict(RECORD, checked_at='2026-10-23T18:00:00Z')
        result = release.assess('42', now=BEFORE, records={'42': record})
        self.assertFalse(result['eligible'])
        self.assertIsNone(result['start_utc'])
        self.assertIsNone(result['expires_at'])

    def test_both_integrity_checks_use_shared_release_gate(self):
        for name in ['scripts/check_board.py', 'tools/check_site.py']:
            self.assertIn('high_release_errors(', (ROOT / name).read_text())
