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
