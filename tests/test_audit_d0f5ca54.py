"""Audit pins for session-d0f5ca54 (task-49 reconciliation, 2026-10-23).

This session ran an independent daily refresh in parallel with five sibling
sessions and landed as a reconciliation onto their merged main. These pins
cover only the net-new contributions that survived that reconciliation:

- no published piece on either track contains the words "model" or
  "verified" (completes FL-152, which scrubbed the root track only);
- FL-154: the SuperLega venue/clock corrections stay corrected;
- FL-155: the /olbg/ EuroLeague records say Round 7 with certified starts,
  BKB-30 no longer misstates TJ Shorts or Valencia's record, and the Spurs
  venue agrees with FL-153;
- BSB-01 names the World Series Game 1 starters;
- the new TEN-902162 analysis piece exists, is >= 30 words and quotes the
  row's current price;
- root and gap refs never collide.
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
        cls.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text())["events"]}
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text())["predictions"]}
        cls.preds_olbg = json.loads((DATA / "predictions-olbg.json").read_text())["predictions"]
        cls.verifs = json.loads((DATA / "verifications.json").read_text())["event_verifications"]
        cls.flagged = {i["id"] for i in json.loads((DATA / "flagged.json").read_text())["items"]}

    def test_no_piece_contains_banned_words(self):
        banned = re.compile(r"model|verified", re.I)
        for ref, p in self.preds.items():
            for field in ("headline", "body", "selection"):
                self.assertIsNone(banned.search(p.get(field) or ""), f"{ref}.{field}")
        for p in self.preds_olbg:
            for field in ("text", "selection"):
                self.assertIsNone(banned.search(p.get(field) or ""), f"{p['match_id']}.{field}")

    def test_fl154_superlega_venue_corrections(self):
        self.assertIn("FL-154", self.flagged)
        self.assertEqual(self.verifs["36994"]["venue"], "Trento, Italy")
        self.assertEqual(self.verifs["36994"]["start_utc"], "2026-10-25T16:00:00Z")
        self.assertEqual(self.verifs["36997"]["venue"], "")
        self.assertEqual(self.verifs["36997"]["start_utc"], "2026-10-25T17:00:00Z")

    def test_fl155_euroleague_olbg_records_say_round_7(self):
        self.assertIn("FL-155", self.flagged)
        self.assertIn("Round 7", self.verifs["535925"]["competition"])
        self.assertIn("Round 7", self.verifs["535926"]["competition"])
        self.assertEqual(self.verifs["535925"]["start_utc"], "2026-10-23T18:15:00Z")
        self.assertEqual(self.verifs["535926"]["start_utc"], "2026-10-23T18:45:00Z")
        body = self.preds["BKB-30"]["body"]
        self.assertNotIn("get point guard TJ Shorts back", body)
        self.assertNotIn("5-1", body)
        self.assertIn("TJ Shorts", body)

    def test_spurs_venue_agrees_with_fl153(self):
        self.assertEqual(self.verifs["534841"]["venue"], "Moody Center, Austin")

    def test_bsb01_names_the_starters(self):
        body = self.preds["BSB-01"]["body"]
        self.assertIn("Nick Martinez", body)
        self.assertIn("Misiorowski", body)
        self.assertNotIn("was not named", body)

    def test_ten_902162_piece_exists_and_quotes_current_price(self):
        piece = self.preds["TEN-902162"]
        self.assertGreaterEqual(len(piece["body"].split()), 30)
        price = self.events["TEN-902162"]["pick"]["price"]
        self.assertIn(f"{price:.2f}", piece["selection"])

    def test_root_and_gap_refs_never_collide(self):
        gap_refs = {r["ref"] for r in json.loads((DATA / "gap_sports.json").read_text())["rows"]}
        self.assertEqual(set(self.events) & gap_refs, set())


if __name__ == "__main__":
    unittest.main()
