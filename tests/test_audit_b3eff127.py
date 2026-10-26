"""Regression pins for the stale-snapshot publication repair."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
BOARD = ROOT / "olbg-board"


class StaleBannerLinkTests(unittest.TestCase):
    def test_stale_banner_link_resolves_from_top_level_pages(self):
        html = (BOARD / "index.html").read_text()
        self.assertIn('SNAPSHOT STALE', html)
        self.assertIn('href="flagged.html">Flagged for review</a>', html)
        self.assertTrue((BOARD / "flagged.html").is_file())

    def test_stale_banner_link_resolves_from_every_sport_page(self):
        pages = sorted((BOARD / "sports").glob("*.html"))
        self.assertTrue(pages, "the board must emit sport pages")
        for page in pages:
            with self.subTest(page=page.name):
                html = page.read_text()
                self.assertIn('SNAPSHOT STALE', html)
                self.assertIn('href="../flagged.html">Flagged for review</a>', html)
                self.assertTrue((page.parent / "../flagged.html").resolve().is_file())


if __name__ == "__main__":
    unittest.main()
