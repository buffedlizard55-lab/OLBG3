"""Audit pins for session-d0f5ca54 (task-46, 2026-10-23 daily refresh).

These pin the load-bearing invariants of the 2026-10-23T16:50Z build so a later
roll-forward has to touch them deliberately:
- the publication clock is the 16:50Z re-observation batch;
- FL-134: the five Pro D2 release records no longer invent a CET clock;
- FL-132: Stormers v Scarlets certifies from the URC list, not a club page;
- the two new NHL rows release HIGH with API-certified clocks and pieces
  that quote the originated prices;
- no published piece on either track contains the words "model" or
  "verified" (the user's standing instruction; 68 fields swept this pass);
- root and gap refs never collide (the DRT-17/18 lesson).
"""
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


class AuditD0f5ca54Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((DATA / "meta.json").read_text())
        cls.rc_doc = json.loads((DATA / "release_checks.json").read_text())
        cls.rc = cls.rc_doc["events"]
        events_doc = json.loads((DATA / "events.json").read_text())
        cls.publication_clock = events_doc["publication_clock"]
        cls.events = {r["ref"]: r for r in events_doc["events"]}
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}
        cls.preds_olbg = json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]
        cls.flagged = {i["id"] for i in json.loads((DATA / "flagged.json").read_text())["items"]}

    def test_publication_clock_is_the_1650z_batch(self):
        self.assertEqual(self.meta["run_id"], "S-20261023-A")
        self.assertEqual(self.rc_doc["checked_at"], "2026-10-23T16:50:00Z")
        self.assertTrue(str(self.publication_clock).startswith("2026-10-23T16:50:00"))

    def test_fl134_prod2_clocks_are_date_only(self):
        for eid in ("609558", "609560", "609561", "609562", "609563"):
            self.assertEqual(self.rc[eid]["kind"], "date_only", eid)
            self.assertIsNone(self.rc[eid]["timezone"], eid)
            self.assertIsNone(self.rc[eid]["time"], eid)
        for ref in ("RGU-02", "RGU-03", "RGU-09"):
            self.assertFalse(self.events[ref]["pick"]["release"]["eligible"], ref)
        self.assertIn("FL-134", self.flagged)

    def test_fl132_stormers_clock_comes_from_the_urc_list(self):
        rec = self.rc["609580"]
        self.assertEqual(rec["timezone"], "Irish time")
        self.assertEqual(rec["time"], "15:00")
        self.assertIn("unitedrugby.com", rec["source"])

    def test_new_nhl_rows_release_high_with_api_clocks(self):
        self.assertEqual(self.rc["199984"]["time"], "00:00")
        self.assertEqual(self.rc["199985"]["time"], "01:00")
        for eid in ("199984", "199985"):
            self.assertEqual(self.rc[eid]["timezone"], "UTC", eid)
            self.assertEqual(self.rc[eid]["date"], "2026-10-24", eid)
            self.assertIn("api-web.nhle.com", self.rc[eid]["source"], eid)
        for ref, price, us in (("IHO-30", 1.55, "-182"), ("IHO-31", 1.72, "-139")):
            pick = self.events[ref]["pick"]
            self.assertEqual(pick["confidence"], "HIGH", ref)
            self.assertEqual(pick["price"], price, ref)
            self.assertTrue(pick["release"]["eligible"], ref)
            piece = self.preds[ref]
            self.assertGreaterEqual(len(piece["body"].split()), 30, ref)
            self.assertIn(f"{price:.2f}", piece["selection"], ref)
            self.assertIn(us, piece["selection"], ref)

    def test_no_piece_contains_banned_words(self):
        banned = re.compile(r"model|verified", re.I)
        for ref, p in self.preds.items():
            for field in ("headline", "body", "selection"):
                self.assertIsNone(banned.search(p.get(field) or ""), f"{ref}.{field}")
        for p in self.preds_olbg:
            for field in ("text", "selection"):
                self.assertIsNone(banned.search(p.get(field) or ""), f"{p['match_id']}.{field}")

    def test_fl137_nhl_blocks_agree_for_tonights_clubs(self):
        fd = json.loads((DATA / "official.json").read_text())["form_data"]
        a = fd["NHL_standings_2026_10_22"]["teams"]
        b = fd["NHL_standings_2026_10_23"]["teams"]
        a = {k.replace("Montreal Canadiens", "Montréal Canadiens"): v for k, v in a.items()}
        for club in ("Montréal Canadiens", "Chicago Blackhawks", "Colorado Avalanche", "Tampa Bay Lightning"):
            for key in ("gp", "gf", "ga"):
                self.assertEqual(a[club][key], b[club][key], f"{club}.{key}")

    def test_root_and_gap_refs_never_collide(self):
        gap_refs = {r["ref"] for r in json.loads((DATA / "gap_sports.json").read_text())["rows"]}
        root_refs = set(self.events)
        self.assertEqual(root_refs & gap_refs, set())


if __name__ == "__main__":
    unittest.main()
