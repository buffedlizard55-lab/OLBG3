#!/usr/bin/env python3
"""Regression tests for two harvest defects found and repaired in session-d26daaf0 (FL-191, FL-192).

FL-192 (found by writing these tests, not before them)
------------------------------------------------------
``extract_listings.py`` guarded its *capture* path with ``is_relative_to(ROOT)`` but printed its
*harvest* path with a bare ``out.relative_to(ROOT)``. Any ``--out`` outside the repository
therefore wrote the file and then died with ``ValueError`` on the summary line, exiting 1 — which
``scripts/live_refresh.py`` reads as "extraction failed" and aborts on. One ``display_path()``
helper is now used for both paths.

The defect
----------
``scripts/extract_listings.py`` called ``write_tsv()`` unconditionally, so a listing capture that
carried **no** tip cards still produced ``data/raw/olbg-harvest-<stamp>.tsv`` — six comment lines
and zero data rows. ``scripts/live_refresh.py`` then picked captures by name only ("the newest one
by name wins", its own docstring), so an empty capture became the pipeline's harvest. Two things
followed, both reproduced here against the committed evidence:

1. ``tests/test_live_20261023.py::test_live_capture_is_the_newest`` pins the newest harvest
   filename, so the zero-row file turned the unit-test step red. On ``main`` that step runs after
   ``live_refresh.py`` and before the commit step, so an overnight empty capture would have made
   the publish job fail.
2. Any step that resolves "the newest harvest TSV" instead of ``data/meta.json["harvest_file"]``
   would have replaced all 180 published ``/olbg/`` rows with nothing. Only the fact that
   ``tools/build_dataset.py`` reads the pinned ``harvest_file`` kept the board intact — luck, not a
   guard.

The repair
----------
An empty capture is *evidence*, not a *harvest*. ``extract_listings.py`` now writes its
``extract-report.json`` (which is what proves the listings really were empty rather than unread)
and exits ``EMPTY_CAPTURE`` (3) without creating a harvest file, and removes a stale zero-row file
at the target path so a re-run is byte-stable. ``live_refresh.py`` walks captures newest-first and
skips any that yields no rows, falling back to the newest capture that has some.

The evidence these tests pin
----------------------------
``data/raw/live-20261023T2135Z`` is the capture taken on a GitHub Actions runner at
2026-10-23T21:30Z: all 18 in-scope OLBG listings returned HTTP 200 (220-309 KB each) and not one
carried a tip card. That is OLBG's overnight state, independently seen at 19:35Z by another
session's runner capture, and it is not a read failure.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / 'data' / 'raw'
SCRIPTS = ROOT / 'scripts'
sys.path.insert(0, str(SCRIPTS))

import extract_listings  # noqa: E402
import live_refresh  # noqa: E402

EMPTY_CAPTURE = 'live-20261023T2135Z'
POPULATED_CAPTURE = 'live-20261023T1700Z'


def run(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *args],
                          capture_output=True, text=True, cwd=str(ROOT))


class EmptyCaptureEvidence(unittest.TestCase):
    """The committed empty capture must really be empty, and really be a successful read."""

    def setUp(self):
        self.capture = RAW / EMPTY_CAPTURE
        if not (self.capture / 'manifest.json').exists():
            self.skipTest(f'{EMPTY_CAPTURE} not committed; the evidence this class pins is absent')
        self.manifest = json.loads((self.capture / 'manifest.json').read_text(encoding='utf-8'))

    def test_all_eighteen_listings_returned_200_with_real_bytes(self):
        pages = self.manifest['pages']
        self.assertEqual(len(pages), 18, 'the 15 in-scope sports span 18 listing endpoints')
        for page in pages:
            self.assertEqual(page['outcome'], 'captured', page['path'])
            self.assertEqual(page['status'], 200, page['path'])
            self.assertGreater(page['bytes'], 200_000, page['path'])

    def test_zero_tip_cards_across_every_listing(self):
        """0 cards is the finding. If this ever fails, the empty-capture guard needs re-thinking."""
        report = self.capture / 'extract-report.json'
        if not report.exists():
            # Regenerate it deterministically; the script writes the report on both paths.
            self.assertEqual(run('extract_listings.py', '--capture', str(self.capture),
                                 '--out', '/tmp/never-written.tsv').returncode,
                             extract_listings.EMPTY_CAPTURE)
        doc = json.loads(report.read_text(encoding='utf-8'))
        listings = doc['listings']
        self.assertEqual(len(listings), 18)
        self.assertEqual(sum(int(p.get('cards') or 0) for p in listings), 0)
        self.assertEqual(doc.get('parse_gaps'), {},
                         'no parse gaps: the pages were read, they simply held no cards')

    def test_the_served_html_shows_the_empty_state_not_an_error(self):
        text = (self.capture / 'listings' / 'betting-tips_Tennis_3.txt').read_text(encoding='utf-8')
        self.assertIn('No tips found.', text)
        self.assertNotIn('Show Expired Events\nEvents\nSelection', text,
                         'the tips table header must not be present on an empty listing')

    def test_the_empty_state_is_an_absence_of_tips_not_a_client_render_gap(self):
        """FL-193. Same script, same User-Agent, same URL, four hours apart: the earlier capture
        carries 8 server-rendered cards, the later one carries none. If the table were rendered
        only in the browser, the earlier capture could not have carried cards — so the later
        empty state means OLBG had no tips listed, not that tips existed unseen."""
        earlier = RAW / 'live-20261023T1700Z' / 'listings' / 'betting-tips_Tennis_3.html'
        later = self.capture / 'listings' / 'betting-tips_Tennis_3.html'
        if not earlier.exists() or not later.exists():
            self.skipTest('one of the two compared captures is not committed')
        marker = 'class="grd tip content-visibility-auto"'
        self.assertEqual(earlier.read_text(encoding='utf-8').count(marker), 8,
                         'the server does render tip cards when there are any')
        self.assertEqual(later.read_text(encoding='utf-8').count(marker), 0)
        self.assertEqual(earlier.read_text(encoding='utf-8').count('itemprop="startDate"'), 8)
        self.assertEqual(later.read_text(encoding='utf-8').count('itemprop="startDate"'), 0)
        # The later page is still a real, fully served listing — nav and editorial links intact.
        self.assertGreater(later.read_text(encoding='utf-8').count('event_id='), 0)


class ExtractListingsGuard(unittest.TestCase):
    def test_exit_code_is_distinct_from_failure(self):
        self.assertEqual(extract_listings.EMPTY_CAPTURE, 3)
        self.assertNotEqual(extract_listings.EMPTY_CAPTURE, 0)
        self.assertNotEqual(extract_listings.EMPTY_CAPTURE, 1)

    def test_empty_capture_writes_no_harvest_but_keeps_the_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'olbg-harvest-empty.tsv'
            result = run('extract_listings.py', '--capture', str(RAW / EMPTY_CAPTURE),
                         '--out', str(out))
            self.assertEqual(result.returncode, extract_listings.EMPTY_CAPTURE, result.stdout)
            self.assertFalse(out.exists(), 'an empty capture must not create a harvest file')
            self.assertIn('no harvest written', result.stdout)
        self.assertTrue((RAW / EMPTY_CAPTURE / 'extract-report.json').exists(),
                        'the evidence of the empty state must survive')

    def test_stale_zero_row_harvest_is_removed_so_reruns_are_stable(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'olbg-harvest-empty.tsv'
            out.write_text('# header only\n# second comment\n', encoding='utf-8')
            result = run('extract_listings.py', '--capture', str(RAW / EMPTY_CAPTURE),
                         '--out', str(out))
            self.assertEqual(result.returncode, extract_listings.EMPTY_CAPTURE)
            self.assertFalse(out.exists())
            self.assertIn('left by an earlier run', result.stdout)

    def test_out_path_outside_the_repo_does_not_crash(self):
        """FL-192: the summary line called out.relative_to(ROOT) unguarded, so an --out outside
        the repo wrote the file and then died with ValueError, exiting 1."""
        capture = RAW / POPULATED_CAPTURE
        if not (capture / 'manifest.json').exists():
            self.skipTest(f'{POPULATED_CAPTURE} not committed')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'outside-the-repo.tsv'
            result = run('extract_listings.py', '--capture', str(capture), '--out', str(out))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn(str(out), result.stdout,
                          'the summary must print the absolute path, not raise on it')
            self.assertTrue(out.exists())

    def test_allow_empty_still_writes_when_explicitly_asked(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'olbg-harvest-empty.tsv'
            result = run('extract_listings.py', '--capture', str(RAW / EMPTY_CAPTURE),
                         '--out', str(out), '--allow-empty')
            self.assertEqual(result.returncode, 0, result.stdout)
            self.assertTrue(out.exists())
            data_rows = [l for l in out.read_text(encoding='utf-8').splitlines()
                         if l.strip() and not l.startswith('#')]
            self.assertEqual(data_rows, [])

    def test_a_populated_capture_is_unaffected_by_the_guard(self):
        capture = RAW / POPULATED_CAPTURE
        if not (capture / 'manifest.json').exists():
            self.skipTest(f'{POPULATED_CAPTURE} not committed')
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / 'olbg-harvest-populated.tsv'
            result = run('extract_listings.py', '--capture', str(capture), '--out', str(out))
            self.assertEqual(result.returncode, 0, result.stdout)
            data_rows = [l for l in out.read_text(encoding='utf-8').splitlines()
                         if l.strip() and not l.startswith('#')]
            self.assertGreater(len(data_rows), 100)

    def test_no_committed_harvest_tsv_has_zero_data_rows(self):
        """The published state: every harvest file in data/raw carries rows."""
        offenders = []
        for path in sorted(RAW.glob('olbg-harvest-*.tsv')):
            rows = [l for l in path.read_text(encoding='utf-8').splitlines()
                    if l.strip() and not l.startswith('#')]
            if not rows:
                offenders.append(path.name)
        self.assertEqual(offenders, [],
                         'a zero-row harvest file would be picked up by name-based resolution')


class LiveRefreshFallback(unittest.TestCase):
    def test_cards_in_reads_the_committed_report(self):
        if not (RAW / EMPTY_CAPTURE / 'extract-report.json').exists():
            self.skipTest('empty capture not yet extracted')
        self.assertEqual(live_refresh.cards_in(RAW / EMPTY_CAPTURE), 0)
        populated = RAW / POPULATED_CAPTURE
        if (populated / 'extract-report.json').exists():
            self.assertGreater(live_refresh.cards_in(populated), 0)

    def test_cards_in_returns_none_for_an_unextracted_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(live_refresh.cards_in(Path(tmp)))

    def test_candidates_are_newest_first(self):
        found = live_refresh.candidates('live-*')
        self.assertTrue(found)
        names = [p.name for p in found]
        self.assertEqual(names, sorted(names, reverse=True))

    def test_check_picks_a_capture_with_cards_not_the_newest_empty_one(self):
        result = run('live_refresh.py', '--check')
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn('no tip cards', result.stdout,
                      'the empty capture must be named as skipped, not silently chosen')
        chosen = [l for l in result.stdout.splitlines() if l.startswith('harvest :')]
        self.assertEqual(len(chosen), 1, result.stdout)
        self.assertNotIn(EMPTY_CAPTURE, chosen[0],
                         'an empty capture must never be selected as the harvest')
        if (RAW / EMPTY_CAPTURE / 'extract-report.json').exists():
            # The chosen capture must be a POPULATED one. It is no longer required to be the
            # 2026-10-23 primary: once a newer populated capture is committed it becomes the
            # harvest this check selects, and the 10-23 file stays in the archive untouched.
            self.assertTrue(chosen[0].split('harvest :')[-1].strip().startswith('data/raw/live-'))

    def test_the_live_primary_harvest_is_unchanged_by_an_empty_capture(self):
        """The whole point: the board keeps the rows the populated capture produced."""
        meta = json.loads((ROOT / 'data' / 'meta.json').read_text(encoding='utf-8'))
        before = meta['harvest_file']
        result = run('live_refresh.py', '--check')
        self.assertEqual(result.returncode, 0, result.stdout)
        after = json.loads((ROOT / 'data' / 'meta.json').read_text(encoding='utf-8'))['harvest_file']
        self.assertEqual(before, after, '--check must not repoint the primary harvest')
        self.assertTrue(before.startswith('raw/olbg-harvest-'), before)
        matches = json.loads((ROOT / 'data' / 'matches.json').read_text(encoding='utf-8'))
        # Same-day SvelteKit supplementary captures (session-b322f52e) may add rows above 180,
        # never reduce below the 180-row primary + 16:30Z floor.
        self.assertGreaterEqual(len(matches), 150,
                                'an empty capture must not reduce the published /olbg/ row count')

    def test_live_primary_capture_maps_the_pinned_harvest_back_to_its_capture(self):
        meta = json.loads((ROOT / 'data' / 'meta.json').read_text(encoding='utf-8'))
        name = meta['harvest_file'].rsplit('/', 1)[-1]
        expected = 'live-' + name[len('olbg-harvest-'):-len('.tsv')]
        self.assertEqual(live_refresh.live_primary_capture(), expected)

    def test_live_primary_capture_is_none_when_the_pin_is_not_a_live_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            meta = Path(tmp) / 'meta.json'
            meta.write_text(json.dumps({'harvest_file': 'raw/some-agent-file.tsv'}), encoding='utf-8')
            real = live_refresh.ROOT
            try:
                live_refresh.ROOT = Path(tmp)
                self.assertIsNone(live_refresh.live_primary_capture())
            finally:
                live_refresh.ROOT = real

    def test_falling_back_to_the_published_primary_does_not_renew_release_evidence(self):
        """Re-stamping after model.py desynchronises the stored release blocks from the evidence
        scripts/check_board.py recomputes, and that integrity check rightly fails. Falling back to a
        capture that is already the live primary adds no fact, so it must not re-verify."""
        if not (RAW / EMPTY_CAPTURE / 'extract-report.json').exists():
            self.skipTest('empty capture not yet extracted')
        before = (ROOT / 'data' / 'release_checks.json').read_bytes()
        result = run('live_refresh.py')
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn('verification skipped', result.stdout, result.stdout)
        self.assertEqual((ROOT / 'data' / 'release_checks.json').read_bytes(), before,
                         'release evidence must not be rewritten by a fallback that adds nothing')

    def test_the_primary_harvest_is_reextracted_byte_identically(self):
        """Determinism: choosing the older capture again must not alter the committed harvest."""
        if not (RAW / POPULATED_CAPTURE / 'manifest.json').exists():
            self.skipTest(f'{POPULATED_CAPTURE} not committed')
        tsv = RAW / 'olbg-harvest-20261023T1700Z.tsv'
        if not tsv.exists():
            self.skipTest('primary harvest TSV not committed')
        before = tsv.read_bytes()
        self.assertEqual(run('live_refresh.py').returncode, 0)
        self.assertEqual(tsv.read_bytes(), before,
                         'a re-run of the same capture must reproduce the same bytes')


if __name__ == '__main__':
    unittest.main()
