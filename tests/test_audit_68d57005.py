"""Regression pins for session-68d57005, task-68d57005 (2026-10-24): scheduled-main CI diagnosis.

Context (FL-201, first drafted as FL-199, renumbered at merge because session-aa934191
published FL-199/FL-200 first): tests/test_audit_ebe6dc9c.py::HighCandidateScan asserted
the verified + upcoming + in-band non-HIGH scan equals exactly ["BKB-17", "VOL-26"] against
the LIVE release status. BKB-17 (HOU Rockets @ SA Spurs) tipped off Fri 23 Oct 2026
9:30 PM ET per the NBA.com schedule the row cites, so at any build on/after
2026-10-24T01:30Z the release gate correctly marks it 'past_date', the scan returns
["VOL-26"], and the strict-equality pin failed - red-ing four consecutive scheduled
'Verify and publish dashboard' runs on main (40046381418 / 40068077765 / 40088120634 /
40103014276) at the unit-tests step, each with every rebuild step green.

This session reproduced and diagnosed the failure locally (docs/audit-68d57005.md) and
had its own subset-assertion repair ready when session-aa934191's frozen-clock repair
landed first on main as PR #165: their pin evaluates the 2026-10-23T21:32Z audit instant
via release.assess(now=historical), so the strict historical list equality survives clock
advance by construction. That mechanism is NOT replaced here; these pins corroborate the
shared root cause and pin the invariants both sessions agree on:

  * the frozen-clock repair is present and pins its historical instant explicitly;
  * BKB-17's expiry is documented on the row itself (NBA.com tip-off + venue quoted,
    release 'past_date' with the reason text, never deleted, never outcome-inferred);
  * the same live scan logic used by the original failing pin can never contain BKB-17
    again at any build after its tip-off;
  * every row the live scan returns is still non-HIGH / upcoming / verified / in-band;
  * FL-201 is registered verbatim, is the highest id, duplicates nothing, and this
    session's audit doc cites only FL ids that exist.
"""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DOCS = ROOT / "docs"


def live_scan_candidates():
    """Byte-equivalent to the scan the original dated pin used (pre-repair shape)."""
    events = json.loads((DATA / "events.json").read_text())["events"]
    candidates = []
    for r in events:
        pk = r.get("pick") or {}
        rel = pk.get("release") or {}
        if pk.get("confidence") == "HIGH" or rel.get("status") != "upcoming":
            continue
        price = pk.get("price")
        if price is None or not (1.40 <= price <= 101.0):
            continue
        if (r.get("verification") or {}).get("status") != "verified":
            continue
        candidates.append(r["ref"])
    return candidates


class FrozenClockRepairIsPresent(unittest.TestCase):
    """Corroborates PR #165's mechanism instead of replacing it."""

    def test_historical_pin_exists_and_freezes_the_audit_instant(self):
        import test_audit_ebe6dc9c as upstream
        self.assertTrue(hasattr(upstream.HighCandidateScan,
                                "test_historical_candidate_scan_is_stable_as_publication_clock_advances"))
        src = (ROOT / "tests" / "test_audit_ebe6dc9c.py").read_text()
        self.assertIn("datetime(2026, 10, 23, 21, 32", src)  # the audit instant is explicit
        self.assertIn("assess(", src)                        # evaluated via the release gate
        self.assertIn('["BKB-17", "VOL-26"]', src)           # strict historical equality kept

    def test_historical_pin_passes_against_current_tree(self):
        import test_audit_ebe6dc9c as upstream
        case = upstream.HighCandidateScan(
            "test_historical_candidate_scan_is_stable_as_publication_clock_advances")
        case.test_historical_candidate_scan_is_stable_as_publication_clock_advances()


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

    def test_bkb17_never_in_live_scan_again(self):
        self.assertNotIn("BKB-17", live_scan_candidates())

    def test_every_live_scanned_row_keeps_the_pin_invariants(self):
        events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        for ref in live_scan_candidates():
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

    def test_fl201_registered_and_highest(self):
        ids = [i["id"] for i in self.items]
        self.assertEqual(len(ids), len(set(ids)), "duplicate FL ids in the register")
        fl201 = [i for i in self.items if i["id"] == "FL-201"]
        self.assertEqual(len(fl201), 1)
        item = fl201[0]
        self.assertEqual(item.get("original_id"), "FL-199")  # renumber record kept
        self.assertEqual(item["status"], "resolved")
        self.assertEqual(item["affected_ids"], ["BKB-17"])
        self.assertIn("past_date", item["detail"])
        self.assertIn("PR #165", item["detail"])
        self.assertEqual(max(int(i.split("-")[1]) for i in ids), 201)
        for src in item["sources"]:
            self.assertTrue(src["url"].startswith("https://"), src)

    def test_session_audit_doc_cites_existing_ids(self):
        text = (DOCS / "audit-68d57005.md").read_text()
        known = {i["id"] for i in self.items}
        cited = set(re.findall(r"\bFL-\d{3}\b", text))
        self.assertLessEqual(cited, known, f"audit doc cites unknown ids: {cited - known}")
        self.assertIn("FL-201", cited)


if __name__ == "__main__":
    unittest.main()
