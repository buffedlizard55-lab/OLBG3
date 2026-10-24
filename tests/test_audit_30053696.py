"""Audit pins for session-30053696 (zero-HIGH sports pass, 2026-10-24).

This session owns Tennis / Cricket / Darts / Snooker / Golf / Greyhounds / Rugby League.
Only Pakistan v England (event 188838) cleared an allowlisted, timezone-qualified official
clock plus both-sides ICC ratings inside the HIGH band. Shortfall is published as FL-209..215.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
import release  # noqa: E402


class Session30053696Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))
        cls.ver = json.loads((DATA / "verifications.json").read_text(encoding="utf-8"))
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]}
        cls.olbg = {p["match_id"]: p for p in json.loads((DATA / "predictions-olbg.json").read_text(encoding="utf-8"))["predictions"]}
        cls.flagged = {i["id"]: i for i in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
        cls.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        cls.lines = {r["match_id"]: r for r in json.loads((DATA / "lines.json").read_text(encoding="utf-8"))}

    def test_ecb_www_host_is_a_reviewed_clock_host(self):
        self.assertIn("www.ecb.co.uk", release.OFFICIAL_CLOCK_HOSTS)
        self.assertTrue(release.official_clock_url(
            "https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka"))

    def test_pakistan_england_clock_is_gmt_exact(self):
        rec = self.rc["events"]["188838"]
        self.assertEqual(rec["date"], "2026-10-25")
        self.assertEqual(rec["time"], "08:00")
        self.assertEqual(rec["timezone"], "GMT")
        self.assertEqual(rec["kind"], "exact")
        self.assertEqual(
            rec["source"],
            "https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka",
        )
        self.assertIn("8.00am GMT", rec["quote"])
        self.assertIn("25 October", rec["quote"])
        self.assertIn("Pakistan", rec["quote"])

    def test_icc_odi_table_includes_pakistan_and_england_from_24_oct(self):
        tbl = self.official["form_data"]["ICC_WhiteBall_2026_ratings"]
        self.assertEqual(tbl["retrieved"], "2026-10-24")
        self.assertEqual(tbl["source"], "https://www.icc-cricket.com/rankings/team-rankings/mens/odi")
        self.assertEqual(tbl["teams"]["Pakistan"]["rating"], 103)
        self.assertEqual(tbl["teams"]["England"]["rating"], 93)

    def test_event_188838_is_verified_on_both_tracks(self):
        ev = self.ver["event_verifications"]["188838"]
        self.assertEqual(ev["status"], "verified")
        self.assertEqual(ev["start_utc"], "2026-10-25T08:00:00Z")
        self.assertIn("S-ECB-PAKENG-WATCH", ev["sources"])
        self.assertEqual(self.events["CRK-188838"]["verification"]["status"], "verified")
        self.assertEqual(self.events["CRK-188838"]["pick"]["confidence"], "HIGH")
        self.assertTrue(self.events["CRK-188838"]["pick"]["release"]["eligible"])
        self.assertEqual(self.lines["CRI-188838"]["confidence"], "high")
        self.assertTrue(self.lines["CRI-188838"]["release"]["eligible"])

    def test_written_pieces_clear_the_floor_and_avoid_banned_words(self):
        root = self.preds["CRK-188838"]
        olbg = self.olbg["CRI-188838"]
        self.assertGreaterEqual(len(root["body"].split()), 30)
        self.assertGreaterEqual(len(olbg["text"].split()), 30)
        self.assertEqual(root["status"], "high")
        self.assertEqual(olbg["status"], "high")
        blob = (root["body"] + " " + olbg["text"]).lower()
        self.assertNotIn("model", blob)
        self.assertNotIn("verified", blob)
        self.assertNotEqual(root["body"].strip(), olbg["text"].strip())

    def test_shortfall_flags_are_published(self):
        for fid in ("FL-209", "FL-210", "FL-211", "FL-212", "FL-213", "FL-214", "FL-215"):
            self.assertIn(fid, self.flagged, fid)
        self.assertIn("Cricket", self.flagged["FL-209"]["title"])
        self.assertIn("Tennis", self.flagged["FL-210"]["title"])
        self.assertIn("Darts", self.flagged["FL-211"]["title"])
        self.assertIn("Snooker", self.flagged["FL-212"]["title"])
        self.assertIn("Golf", self.flagged["FL-213"]["title"])
        self.assertIn("Greyhounds", self.flagged["FL-214"]["title"])
        self.assertIn("Rugby League", self.flagged["FL-215"]["title"])


if __name__ == "__main__":
    unittest.main()
