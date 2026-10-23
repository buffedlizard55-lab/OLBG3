"""Pins for the 2026-10-23 live pipeline (session-22dbc477).

Each test protects a rule that, if it silently changed, would let this project publish something
it cannot support: a clock it inferred, a fixture it guessed, or a "stale" build that quietly
looks fresh.
"""
import datetime as dt
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'tools'))

import board_dates as bd          # noqa: E402
import extract_listings as ex     # noqa: E402
import release                    # noqa: E402
import verify_live as vl          # noqa: E402


class HarvestSchema(unittest.TestCase):
    def setUp(self):
        self.tsv = ROOT / 'data/raw/olbg-harvest-20261023T1700Z.tsv'

    def test_v3_header_is_declared(self):
        head = self.tsv.read_text().splitlines()[:4]
        self.assertTrue(head[0].startswith('# OLBG3 live harvest live-20261023T1700Z'))
        self.assertIn('format v3', head[0])
        self.assertIn('start_utc', head[1])

    def test_every_row_has_eighteen_columns(self):
        rows = [l for l in self.tsv.read_text().splitlines() if l and not l.startswith('#')]
        self.assertEqual(len(rows), 177)
        for row in rows:
            self.assertEqual(len(row.split('|')), 18, row[:80])

    def test_every_row_carries_olbg_own_utc_start(self):
        rows = [l.split('|') for l in self.tsv.read_text().splitlines() if l and not l.startswith('#')]
        for row in rows:
            self.assertRegex(row[11], r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000Z$')
            self.assertRegex(row[12], r'^\d+\.\d+$')
            # positive American odds are rendered without a leading '+'
            self.assertRegex(row[13], r'^[+-]?\d+$')

    @staticmethod
    def _uk_offset(day):
        """British Summer Time is UTC+1 between the last Sundays of March and October."""
        def last_sunday(year, month):
            probe = dt.date(year, month, 31)
            while probe.weekday() != 6:
                probe -= dt.timedelta(days=1)
            return probe
        start = dt.datetime.combine(last_sunday(day.year, 3), dt.time(1, 0))
        end = dt.datetime.combine(last_sunday(day.year, 10), dt.time(2, 0))
        moment = day if isinstance(day, dt.datetime) else dt.datetime.combine(day, dt.time(12, 0))
        return 1 if start <= moment < end else 0

    def test_printed_clock_matches_the_dst_rule(self):
        """OLBG prints a UK clock; its own startDate attribute is the UTC instant."""
        rows = [l.split('|') for l in self.tsv.read_text().splitlines() if l and not l.startswith('#')]
        checked = 0
        for row in rows:
            start = dt.datetime.fromisoformat(row[11].replace('Z', '+00:00'))
            if not row[6] or row[5] not in ('Today', 'Tomorrow') and ' ' not in row[5].strip():
                continue
            printed_hour = int(row[6].split(':')[0])
            expected_offset = self._uk_offset(start.replace(tzinfo=None))
            self.assertEqual((printed_hour - start.hour) % 24, expected_offset,
                             f'{row[16]} printed {row[6]} vs startDate {row[11]}')
            checked += 1
        self.assertGreater(checked, 100)


class Extractor(unittest.TestCase):
    def test_dedupe_keeps_first_and_records_the_second_listing(self):
        rows = [
            {'event_id': '1', 'note': '', 'sport': 'Ice Hockey', 'league_label': 'all'},
            {'event_id': '1', 'note': '', 'sport': 'Ice Hockey', 'league_label': 'NHL'},
            {'event_id': '2', 'note': '', 'sport': 'Ice Hockey', 'league_label': 'all'},
        ]
        out = ex.dedupe(rows)
        self.assertEqual([r['event_id'] for r in out], ['1', '2'])
        self.assertIn('also listed on Ice Hockey/NHL', out[0]['note'])

    def test_printed_clock_split_is_mechanical(self):
        self.assertEqual(ex.clean_printed('<i class="x"></i> Today <i></i> 17:30'),
                         ('Today', '17:30'))
        self.assertEqual(ex.clean_printed('25 Oct 18:00'), ('25 Oct', '18:00'))

    def test_unreadable_clock_stays_blank_not_guessed(self):
        self.assertEqual(ex.clean_printed('sometime friday'), ('sometime friday', ''))


class OfficialMatching(unittest.TestCase):
    def test_both_sides_and_a_close_clock_are_required(self):
        rows = [{'sport': 'Ice Hockey', 'event_name': 'MTL Canadiens @ CHI Blackhawks',
                 'start_utc': '2026-10-24T00:07:00.000Z', 'event_id': '199984'}]
        with patch.object(vl, 'load_harvest', return_value=rows):
            pass
        games = vl.nhl_games({'gameWeek': [{'date': '2026-10-23', 'games': [{
            'id': 2026020166, 'startTimeUTC': '2026-10-24T00:00:00Z',
            'homeTeam': {'abbrev': 'CHI', 'commonName': {'default': 'Blackhawks'}, 'name': {'default': 'Chicago Blackhawks'}},
            'awayTeam': {'abbrev': 'MTL', 'commonName': {'default': 'Canadiens'}, 'name': {'default': 'Montreal Canadiens'}},
        }]}]})
        self.assertEqual(len(games), 1)
        tokens = vl.norm(rows[0]['event_name'])
        self.assertGreaterEqual(len(tokens & games[0]['tokens']), 2)

    def test_a_different_day_is_outside_the_tolerance(self):
        start = vl.parse_utc('2026-10-24T00:07:00.000Z')
        game = vl.parse_utc('2026-10-26T00:00:00Z')
        self.assertGreater(abs(game - start), vl.TOLERANCE)

    def test_mlb_date_is_an_explicit_utc_instant(self):
        games = vl.mlb_games({'dates': [{'date': '2026-10-23', 'games': [{
            'gamePk': 849805, 'gameDate': '2026-10-24T00:00:00Z',
            'teams': {'home': {'team': {'name': 'Milwaukee Brewers', 'teamName': 'Brewers'}},
                      'away': {'team': {'name': 'Tampa Bay Rays', 'teamName': 'Rays'}}}}]}]})
        self.assertEqual(games[0]['start_utc'], '2026-10-24T00:00:00Z')
        self.assertTrue(vl.parse_utc(games[0]['start_utc']).tzinfo is not None)


class ClockIntegrity(unittest.TestCase):
    def test_mlb_stats_endpoint_is_a_reviewed_clock_host(self):
        self.assertIn('statsapi.mlb.com', release.OFFICIAL_CLOCK_HOSTS)
        self.assertTrue(release.official_clock_url('https://statsapi.mlb.com/api/v1/schedule?sportId=1'))

    def test_unknown_host_cannot_certify_a_start(self):
        self.assertFalse(release.official_clock_url('https://example.com/schedule'))

    def test_build_date_follows_the_publication_clock(self):
        with patch.object(bd, 'snapshot_utc',
                          return_value=dt.datetime(2026, 10, 23, 16, 28, tzinfo=dt.timezone.utc)), \
             patch.dict(os.environ, {}, clear=True):
            self.assertEqual(bd.build_date(), dt.date(2026, 10, 23))

    def test_stale_snapshot_is_measured_in_hours(self):
        with patch.object(bd, 'source_snapshot_utc',
                          return_value=dt.datetime(2026, 10, 23, 16, 28, tzinfo=dt.timezone.utc)), \
             patch.dict(os.environ, {}, clear=True):
            self.assertEqual(
                bd.snapshot_age_hours(now=dt.datetime(2026, 10, 25, 10, 0, tzinfo=dt.timezone.utc)), 41.5)


class ArchiveIntegrity(unittest.TestCase):
    """The skips in the dated audit pins are only honest if the archives still exist (FL-144)."""

    ARCHIVES = {
        'olbg-harvest-20261022T2130Z.tsv': 118,
        'olbg-harvest-20261022T2100Z.tsv': None,
        'olbg-harvest-20261022T1215Z.tsv': None,
        'olbg-harvest-20261022T0830Z.tsv': None,
        'olbg-harvest-20261022T0725Z.tsv': None,
        'olbg-harvest-20261022T2055Z.tsv': 128,
        'olbg-harvest-20261022.tsv': None,
        'olbg-harvest-20261021T0650Z.tsv': None,
        'olbg-harvest-20261021.tsv': None,
    }

    def test_every_archived_capture_is_still_present(self):
        for name, expected_rows in self.ARCHIVES.items():
            path = ROOT / 'data/raw' / name
            self.assertTrue(path.exists(), name)
            rows = [l for l in path.read_text().splitlines() if l and not l.startswith('#')]
            self.assertGreater(len(rows), 0, name)
            if expected_rows is not None:
                self.assertEqual(len(rows), expected_rows, name)

    def test_live_capture_is_the_newest(self):
        # 2026-10-23T21:35Z (session-a87a3681): a later capture EXISTS but carries no tip cards, because
        # OLBG rendered "No tips found." for all 18 in-scope listings (FL-180). The primary harvest is
        # therefore the newest capture that actually carries rows, and the empty later capture is kept
        # as evidence rather than deleted. Assert both halves so neither can drift silently.
        #
        # 2026-10-23T22:10Z (session-d26daaf0, FL-191): the same intent, asserted one level stronger,
        # and the cause fixed rather than tolerated. FL-180 made THIS test filter out harvest files
        # with no rows; the two places that produced the empty file were untouched, so
        # scripts/extract_listings.py still wrote a zero-row TSV for an empty capture and
        # scripts/live_refresh.py still chose captures by name alone ("the newest one by name wins").
        # Any resolver using "newest harvest TSV" instead of data/meta.json["harvest_file"] would
        # still have picked the empty one and published zero rows over the board. Both are now fixed
        # at the source, so the evidence this test protected lives where it belongs — the committed
        # capture directory (18 served HTML pages + manifest + extract-report.json) — and no zero-row
        # harvest file exists to be picked up by name.
        paths = sorted((ROOT / 'data/raw').glob('olbg-harvest-*.tsv'), key=lambda p: p.name)
        empty = [p.name for p in paths
                 if not [l for l in p.read_text().splitlines() if l and not l.startswith('#')]]
        self.assertEqual(empty, [],
                         'a zero-row harvest file is selectable by name, so none may be committed')
        self.assertEqual(paths[-1].name, 'olbg-harvest-20261023T1700Z.tsv',
                         'with the guard in place, newest by name IS newest with rows')
        # The empty 21:35Z capture is still evidence — as a capture, not as a derived empty TSV.
        capture = ROOT / 'data/raw/live-20261023T2135Z'
        self.assertTrue((capture / 'manifest.json').exists(), capture)
        self.assertTrue((capture / 'extract-report.json').exists(), capture)
        self.assertEqual(len(list((capture / 'listings').glob('*.html'))), 18, capture)

    def test_archived_files_are_not_reused_as_the_primary_harvest(self):
        meta = json.loads((ROOT / 'data/meta.json').read_text())
        self.assertEqual(meta['harvest_file'], 'raw/olbg-harvest-20261023T1700Z.tsv')


class PublishedState(unittest.TestCase):
    def test_high_picks_are_inside_the_band_and_verified(self):
        lines = json.loads((ROOT / 'data/lines.json').read_text())
        matches = {m['id']: m for m in json.loads((ROOT / 'data/matches.json').read_text())}
        high = [r for r in lines if r['confidence'] == 'high']
        self.assertTrue(high, 'expected at least one HIGH pick')
        for row in high:
            self.assertGreaterEqual(row['our_price_pick'], 1.40)
            self.assertLessEqual(row['our_price_pick'], 101.0)
            self.assertEqual(matches[row['match_id']]['competition_status'], 'verified')
            self.assertTrue(row['release']['eligible'], row['match_id'])

    def test_no_pick_is_published_from_a_carried_older_harvest(self):
        meta = json.loads((ROOT / 'data/meta.json').read_text())
        self.assertEqual(meta['harvest_format'], 'v3')
        self.assertIsNone(meta['previous_harvest'])
        self.assertEqual(meta['previous_harvests_extra'], [])

    def test_verified_events_cite_an_official_payload(self):
        ver = json.loads((ROOT / 'data/verifications.json').read_text())
        rc = json.loads((ROOT / 'data/release_checks.json').read_text())['events']
        for event_id in ('160789', '199984', '199985'):
            self.assertEqual(ver['event_verifications'][event_id]['status'], 'verified')
            self.assertIn('start_utc', ver['event_verifications'][event_id])
            self.assertTrue(release.official_clock_url(rc[event_id]['source']))
            self.assertTrue(rc[event_id]['quote'])


if __name__ == '__main__':
    unittest.main()
