"""session-170e6805: executive-summary / pick-quality audit regressions."""
import json, subprocess, sys, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]

class Audit170e6805(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        subprocess.run([sys.executable, str(ROOT/"scripts/audit_170e6805.py")], check=True, capture_output=True)
        cls.a = json.loads((ROOT/"data/audit-170e6805.json").read_text())
        cls.page = (ROOT/"exec-summary.html").read_text()

    def test_covers_all_15_sports(self):
        self.assertEqual(len(self.a["per_sport"]), 15)

    def test_all_fixtures_have_originated_lines(self):
        self.assertEqual(self.a["totals"]["fixtures"], self.a["totals"]["lines"])
        self.assertGreater(self.a["totals"]["fixtures"], 0)

    def test_no_prose_quality_failures(self):
        bad = [i for i in self.a["issues"] if any(k in i["issue"] for k in
               ("under 30 words", "duplicate prose", "banned reader-facing", "no explicit selection", "non-https"))]
        self.assertEqual(bad, [])

    def test_live_high_picks_in_band_and_linked(self):
        self.assertGreaterEqual(len(self.a["live_high"]), 1)
        for p in self.a["live_high"]:
            price = int(str(p["price"]).replace("+", ""))
            self.assertTrue(-250 <= price <= 10000, p)
            self.assertTrue(all(s["url"].startswith("https://") for s in p["sources"]))
            self.assertIn("🎯 PICK", self.page)
            self.assertIn(p["selection"].split("(")[0].strip()[:20], self.page)

    def test_known_flags_present(self):
        txt = json.dumps(self.a["issues"])
        self.assertIn("DAR-32332", txt)  # -333 outside brief band
        self.assertIn("-333", txt)

    def test_shortfalls_published_not_hidden(self):
        # FL-201 lesson: the identity must hold for every state of the board, not just the state
        # on the day it was written. A sport that exceeds its five-pick target cannot offset
        # another sport's shortfall, so the target-facing sum is 75 minus the *capped* counts.
        # The published shortfall per sport is recomputed from those counts and must match; the
        # deduplicated total may not be smaller than the capped sum.
        self.assertIn("shortfall", self.page)
        per_sport = self.a["per_sport"]
        capped = sum(min(5, v["live_high_upcoming"]) for v in per_sport.values())
        self.assertEqual(sum(v["shortfall"] for v in per_sport.values()), 75 - capped)
        self.assertGreaterEqual(self.a["totals"]["live_high_upcoming"], capped)
        for sport, row in per_sport.items():
            self.assertEqual(row["shortfall"], max(0, 5 - row["live_high_upcoming"]), sport)

if __name__ == "__main__":
    unittest.main()
