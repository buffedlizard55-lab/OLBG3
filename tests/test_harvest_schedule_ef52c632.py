"""The source clock must advance by retrieval, not by hourly HTML rebuilds."""
import os
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HarvestSchedule(unittest.TestCase):
    def test_scheduled_request_is_fresh_and_enables_all_probes(self):
        workflow = (ROOT / '.github/workflows/live-harvest.yml').read_text()
        self.assertIn("cron: '3 */4 * * *'", workflow)
        # Execute the exact dependency-free Python used by the request step.
        start = workflow.index('          import json\n')
        end = workflow.index('\n          PY', start)
        code = '\n'.join(line[10:] for line in workflow[start:end].splitlines())
        for event in ('schedule', 'workflow_dispatch', 'push'):
            env = dict(os.environ, GITHUB_EVENT_NAME=event)
            result = subprocess.run([sys.executable, '-c', code], cwd=ROOT,
                                    env=env, text=True, capture_output=True, check=True)
            fields = dict(line.split('=', 1) for line in result.stdout.splitlines())
            if event != 'push':
                self.assertRegex(fields['out'], r'^data/raw/live-\d{8}T\d{6}Z-scheduled$')
                for name in ('capture', 'probe', 'cited'):
                    self.assertEqual(fields[name], 'true')
            else:
                self.assertEqual(fields['out'], json.loads(
                    (ROOT / '.harvest/request.json').read_text())['out'])

    def test_failed_rebase_is_not_masked(self):
        workflow = (ROOT / '.github/workflows/live-harvest.yml').read_text()
        pull = next(line for line in workflow.splitlines() if 'git pull --rebase' in line)
        self.assertNotIn('|| true', pull)


class ZeroPickSafety(unittest.TestCase):
    def test_publication_boundary_rejects_unsupported_picks(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import pick_surface
        source = 'https://api-web.nhle.com/v1/schedule/2026-10-26'
        release = {'eligible': True, 'source': source}
        text = ' '.join(['Synthetic test input not a sporting prediction'] * 6)
        sources = [{'url': source}]
        self.assertEqual(pick_surface.pick_problem('HIGH', release, 1.8, text, sources), '')
        cases = [
            ('LOW', release, 1.8, text, sources),
            ('HIGH', {'eligible': False}, 1.8, text, sources),
            ('HIGH', release, 1.8, '', sources),
            ('HIGH', release, 1.8, 'too short', sources),
            ('HIGH', release, 1.2, text, sources),
            ('HIGH', release, 102, text, sources),
            ('HIGH', release, 1.8, text, []),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertTrue(pick_surface.pick_problem(*args))

    def test_empty_shortlist_says_no_pick_without_fake_rows(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import pick_surface
        html = pick_surface.summary_table([])
        self.assertIn('No written pick passes every publication gate', html)
        self.assertNotIn("data-state='pick'", html)


class CapturePromotion(unittest.TestCase):
    def test_new_primary_preserves_previous_sources_and_is_idempotent(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import live_refresh
        capture = ROOT / 'data/raw/live-20261026T2020Z-ef52c632'
        tsv = ROOT / 'data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv'
        old = {'harvest_file': 'raw/older.tsv', 'harvest_format': 'v3',
               'harvest_completed_utc': '2026-10-24T20:00:00Z',
               'olbg_locale_date': '2026-10-24', 'previous_harvest': {'file': 'raw/first.tsv'}}
        result = live_refresh.promote_capture(old, capture, tsv)
        self.assertEqual(result['harvest_file'], str(tsv.relative_to(ROOT / 'data')))
        self.assertEqual(result['previous_harvest']['file'], 'raw/older.tsv')
        self.assertEqual(result['supplementary_harvests'][0], old['previous_harvest'])
        self.assertEqual(live_refresh.promote_capture(result, capture, tsv), result)

    def test_daily_board_does_not_publish_old_capture_as_high(self):
        import datetime as dt
        sys.path.insert(0, str(ROOT / 'scripts'))
        import build_daily
        res = json.loads((ROOT / 'data/daily/research-20261025.json').read_text())
        rows = build_daily.read_capture(res['capture'])
        row = next(r for r in rows if r['event_id'] == '188852')
        clock = dt.datetime(2026, 10, 26, 20, 0, tzinfo=dt.timezone.utc)
        result = build_daily.evaluate(row, res['rows']['188852'], clock, res['captured_at_utc'])
        self.assertNotEqual(result['confidence'], 'HIGH')
        self.assertTrue(any('24 hours old' in r for r in result['reasons']))


class CurrentNHLResearch(unittest.TestCase):
    def test_new_fixture_sources_resolve_to_the_capture_actually_read(self):
        ledger = json.loads((ROOT / 'data/verifications.json').read_text())
        sources = {s['id']: s for s in ledger['sources']}
        for eid in ('200101', '200102', '200103', '200104', '200105', '200111', '200112'):
            for sid in ledger['event_verifications'][eid]['sources']:
                # Follow the active observation, not a frozen source ID: a later genuine
                # reread may replace it without breaking scheduled publication.
                source = sources[sid]
                probe_file = Path(source['probe_file'])
                self.assertIn(probe_file.parts[1], sid)
                self.assertTrue(source['url'].startswith('https://api-web.nhle.com/v1/schedule/'))
                self.assertTrue((ROOT / 'data' / probe_file).exists())

    def test_all_new_probabilities_recompute_from_official_records(self):
        spec = json.loads((ROOT / 'data/pricing-ef52c632.json').read_text())
        standings = json.loads((ROOT / 'data' / spec['source_file']).read_text())['standings']
        teams = {r['teamAbbrev']['default']: r for r in standings}
        pieces = {p['match_id']: p for p in json.loads((ROOT / 'data/patches/picks-ef52c632.json').read_text())}
        self.assertEqual(len(spec['rows']), 7)
        for row in spec['rows']:
            h, a = teams[row['home']], teams[row['away']]
            self.assertEqual((row['home_w'], row['home_gp']), (h['wins'], h['gamesPlayed']))
            self.assertEqual((row['away_w'], row['away_gp']), (a['wins'], a['gamesPlayed']))
            qh = (h['wins'] + 1) / (h['gamesPlayed'] + 2)
            qa = (a['wins'] + 1) / (a['gamesPlayed'] + 2)
            log5 = qh * (1-qa) / (qh * (1-qa) + qa * (1-qh))
            ph = .5 + .5 * (log5-.5) + .03
            self.assertAlmostEqual(row['p_home'], ph)
            self.assertEqual(row['p_pick'], round(max(ph, 1-ph), 4))
            self.assertEqual(row['price'], round(.95 / row['p_pick'], 2))
            self.assertGreaterEqual(len(pieces[row['match_id']]['text'].split()), 30)
