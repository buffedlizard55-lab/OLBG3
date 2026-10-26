"""Regression pins for stale-snapshot links, at explicit stale AND fresh ages.

The source capture may genuinely advance. Exercise the actual banner function with a
controlled age rather than requiring every newly published snapshot to remain stale.
"""
import ast
import html
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / 'olbg-board'


def banner(depth, age):
    tree = ast.parse((ROOT / 'tools/build_site.py').read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'stale_banner')
    namespace = {'snapshot_age_hours': lambda: age, 'E': html.escape,
                 'RUN': json.loads((ROOT / 'data/meta.json').read_text())}
    exec(compile(ast.Module(body=[node], type_ignores=[]), '<actual stale_banner>', 'exec'), namespace)
    return namespace['stale_banner'](depth)


class StaleBannerLinkTests(unittest.TestCase):
    def test_stale_banner_link_resolves_from_top_level_pages(self):
        markup = banner(0, 48)
        self.assertIn('SNAPSHOT STALE', markup)
        self.assertIn('href="flagged.html">Flagged for review</a>', markup)
        self.assertTrue((BOARD / 'flagged.html').is_file())

    def test_stale_banner_link_resolves_from_every_sport_page(self):
        pages = sorted((BOARD / 'sports').glob('*.html'))
        self.assertTrue(pages)
        markup = banner(1, 48)
        self.assertIn('SNAPSHOT STALE', markup)
        self.assertIn('href="../flagged.html">Flagged for review</a>', markup)
        for page in pages:
            self.assertTrue((page.parent / '../flagged.html').resolve().is_file())

    def test_fresh_capture_is_not_falsely_labelled_stale(self):
        self.assertEqual(banner(0, 1), '')
        self.assertEqual(banner(1, 1), '')
