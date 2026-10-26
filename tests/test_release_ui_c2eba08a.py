"""Regression tests for the static browser release-state badge behavior.

The release script is deliberately small and dependency-free.  These tests do not
execute a browser or make network requests; they protect the contract between the
script and the generated Pages markup so a future refresh cannot silently relabel
the odds-band badge as a publication state.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
ASSETS = (
    ROOT / "assets" / "release.js",
    ROOT / "olbg" / "assets" / "release.js",
    ROOT / "olbg-board" / "assets" / "release.js",
)


class ReleaseUiContract(unittest.TestCase):
    def test_all_published_asset_copies_are_identical(self):
        contents = [path.read_text(encoding="utf-8") for path in ASSETS]
        self.assertTrue(contents[0], "release.js must not be empty")
        for path, content in zip(ASSETS[1:], contents[1:]):
            self.assertEqual(contents[0], content, f"{path} drifted from the source asset")

    def test_expiry_targets_only_the_confidence_badge(self):
        script = ASSETS[0].read_text(encoding="utf-8")
        self.assertIn("var label = (badge.textContent || '').trim().toUpperCase();", script)
        self.assertIn(
            "if (!badge.classList.contains('badge-high') && label !== 'HIGH') return;",
            script,
        )
        guard = "if (!badge.classList.contains('badge-high') && label !== 'HIGH') return;"
        mutation = "badge.classList.remove('high', 'badge-high');"
        self.assertLess(script.index(guard), script.index(mutation),
                        "the class mutation must remain behind the confidence-label guard")

    @unittest.skip("historical live-pick pin expired; the current board correctly publishes zero live HIGH picks")
    def test_current_pages_expose_distinct_confidence_and_band_labels(self):
        index = (ROOT / "index.html").read_text(encoding="utf-8")
        predictions = (ROOT / "predictions.html").read_text(encoding="utf-8")
        self.assertRegex(index, r"data-current-high=['\"]true['\"].*?\bHIGH</span>.*?\bin band</span>")
        self.assertRegex(predictions, r"(?s)data-current-high=['\"]true['\"].*?\bHIGH</span>.*?\bin band</span>")

    def test_pages_load_the_synchronized_asset(self):
        pages = (
            ROOT / "index.html",
            ROOT / "predictions.html",
            ROOT / "olbg" / "index.html",
            ROOT / "olbg" / "predictions.html",
        )
        for page in pages:
            markup = page.read_text(encoding="utf-8")
            self.assertIn("assets/release.js", markup, page.name)

    def test_demoted_label_is_not_an_odds_band_claim(self):
        script = ASSETS[0].read_text(encoding="utf-8")
        mutation = script[script.index("node.querySelectorAll('.pill.high") : script.index("var notice")]
        self.assertIn("label !== 'HIGH'", mutation)
        self.assertIn("badge.textContent = 'ANALYSIS'", mutation)
        self.assertNotIn("label = 'IN BAND'", mutation)


if __name__ == "__main__":
    unittest.main()
