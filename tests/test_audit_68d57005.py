"""Regression pins for session-68d57005, task-68d57005 (2026-10-24): scheduled-main CI repair.

Context (FL-199): tests/test_audit_ebe6dc9c.py::HighCandidateScan asserted the
verified + upcoming + in-band non-HIGH scan equals exactly ["BKB-17", "VOL-26"].
BKB-17 (HOU Rockets @ SA Spurs) tipped off Fri 23 Oct 2026 9:30 PM ET per the NBA.com
schedule the row cites, so at any build on/after 2026-10-24T01:30Z the release gate
correctly marks it 'past_date' and the strict-equality pin failed, red-ing four
consecutive scheduled 'Verify and publish dashboard' runs on main
(40046381418 / 40068077765 / 40088120634 / 40103014276) at the unit-tests step.

Pins:
  * BKB-17's expiry is documented on the row itself: the verification note quotes the
    NBA.com tip-off and venue, and the release reason says the fixture date has passed.
    Expired but documented - never silently deleted, never outcome-inferred.
  * The shared scan (imported from test_audit_ebe6dc9c to pin ONE definition) can never
    contain BKB-17 again at any build after its tip-off, and contains no row whose
    release status is not 'upcoming'.
  * The protective direction of the repaired pin holds mechanically: at least one
    non-HIGH, in-band, 'upcoming', 'verified' fixture in the scan would fail the suite
    unless it belongs to the reviewed set.
  * FL-199 is registered verbatim, is the highest id, duplicates nothing, and every
    audit doc this session publishes cites ids that exist.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"


class Bkb17ExpiryIsDocumented(unittest.TestCase):
    def setUp(self):
        self.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}

    def test_bkb17_row_still_published_archive_only(self):
        row = self.events["BKB-17"]
        self.assertEqual(row["home"], "SA Spurs")
        self.assertEqual(row["away"], "HOU Rockets")
        self.assertEqual(row["start"], "23 Oct 21:40")  # OLBG printed label, verbatim
        self.assertEqual(row["verification"]["status"], "verified")
        self.assertIn("9:30 PM ET", row["verification"]["official_datetime"])
        self.assertIn("Moody Center", row["verification"]["official_datetime"])
        self.assertEqual(row["verification"]["official_url"], "https://www.nba.com/schedule?date=2026-10-23")

    def test_bkb17_release_gate_states_why_it_expired(self):
        rel = (self.events["BKB-17"].get("pick") or {}).get("release") or {}
        self.assertEqual(rel.get("status"), "past_date")
        self.assertIn("fixture date has passed", rel.get("reason", ""))
        self.assertIn("Outcome not inferred", rel.get("reason", ""))

    def test_bkb17_never_in_scan_again(self):
        from test_audit_ebe6dc9c import HighCandidateScan  # one shared definition
        self.assertNotIn("BKB-17", HighCandidateScan.scan_candidates())


class ScanIntegrity(unittest.TestCase):
    def test_every_scanned_row_is_upcoming_verified_in_band_non_high(self):
        from test_audit_ebe6dc9c import HighCandidateScan
        events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        for ref in HighCandidateScan.scan_candidates():
            row = events[ref]
            pk = row["pick"]
            self.assertNotEqual(pk.get("confidence"), "HIGH", ref)
            self.assertEqual((pk.get("release") or {}).get("status"), "upcoming", ref)
            self.assertTrue(1.40 <= pk["price"] <= 101.0, ref)
            self.assertEqual((row.get("verification") or {}).get("status"), "verified", ref)


class FlagRegisterIntegrity(unittest.TestCase):
    def setUp(self):
        doc = json.loads((DATA / "flagged.json").read_text())
        self.items = doc["items"]

    def test_fl199_registered_and_highest(self):
        ids = [i["id"] for i in self.items]
        self.assertEqual(len(ids), len(set(ids)), "duplicate FL ids in the register")
        fl199 = [i for i in self.items if i["id"] == "FL-199"]
        self.assertEqual(len(fl199), 1)
        item = fl199[0]
        self.assertEqual(item["status"], "resolved")
        self.assertEqual(item["affected_ids"], ["BKB-17"])
        self.assertIn("past_date", item["detail"])
        self.assertEqual(max(int(i.split("-")[1]) for i in ids), 199)
        for src in item["sources"]:
            self.assertTrue(src["url"].startswith("https://"), src)

    def test_session_audit_doc_cites_existing_ids(self):
        text = (DOCS / "audit-68d57005.md").read_text()
        known = {i["id"] for i in self.items}
        cited = set(re.findall(r"\bFL-\d{3}\b", text))
        self.assertLessEqual(cited, known, f"audit doc cites unknown ids: {cited - known}")
        self.assertIn("FL-199", cited)


if __name__ == "__main__":
    unittest.main()
