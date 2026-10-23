"""Audit pins for the 2026-10-23 daily cycle (session-beb7787b).

Everything asserted here is a committed data fact produced by this session's harvest,
re-observations and corrections. Later sessions may relax clock-dependent assertions as the
publication clock moves, as this session did for earlier pins.
"""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

NEW_VERIFIED = {
    # NBA.com schedule 2026-10-23
    "BKB-33", "BKB-34", "BKB-35", "BKB-36", "BKB-37", "BKB-38", "BKB-39", "BKB-40", "BKB-41",
    # NHL schedule API
    "IHO-30", "IHO-31",
    # URC fixtures-in-full / PREM Rugby fixtures
    "RGU-19", "RGU-20", "RGU-22", "RGU-23",
    # WST matches / WTA order-of-play PDFs
    "SNK-15", "SNK-16", "TEN-53", "TEN-54", "TEN-55", "TEN-56",
}
NEW_UNVERIFIED = {
    "IHO-32", "IHO-33", "IHO-34", "IHO-35", "IHO-36", "IHO-37", "IHO-38", "IHO-39", "IHO-40", "IHO-41", "IHO-42",
    "CRK-19", "CRK-20", "CRK-21", "CRK-22", "CRK-23", "CRK-24",
    "HBL-39", "HBL-40", "HBL-41", "HBL-42", "HBL-43",
    "VOL-36", "VOL-37", "VOL-38", "VOL-39", "VOL-40", "VOL-41", "VOL-42", "VOL-43", "VOL-44",
    "BKB-42", "BKB-43", "RGU-21", "TEN-49", "TEN-50", "TEN-51", "TEN-52", "TEN-57",
    "DRT-21", "DRT-22", "DRT-23", "DRT-24",
}
LIVE_HIGH = {"BSB-01", "BKB-29", "BKB-30", "GAF-01", "RGU-14", "VOL-27", "VOL-28", "VOL-29"}


class DailyCycleBeb7787bTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
        cls.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]}
        cls.flagged = {i["id"]: i for i in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
        cls.official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))

    def test_harvest_chain_head_is_the_23_oct_capture(self):
        self.assertEqual(self.meta["harvest_file"], "raw/olbg-harvest-20261023T1630Z.tsv")
        self.assertEqual(self.meta["olbg_locale_date"], "2026-10-23")
        self.assertEqual(self.meta["run_id"], "S-20261023-A")
        self.assertEqual(self.meta["previous_harvest"]["file"], "raw/olbg-harvest-20261022T2130Z.tsv")
        raw = (DATA / self.meta["harvest_file"]).read_text(encoding="utf-8")
        rows = [l for l in raw.splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(len(rows), 180)
        self.assertTrue((ROOT / "docs/harvest-20261023-1630z.tsv").exists())

    def test_new_rows_verification_split(self):
        for ref in NEW_VERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "verified", ref)
            self.assertIn(self.events[ref]["verification"]["source_tier"], {"official", "club-official"}, ref)
        for ref in NEW_UNVERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "unverified", ref)
            self.assertEqual(self.events[ref]["verification"]["official_url"], "", ref)
            self.assertNotEqual(self.events[ref]["pick"]["confidence"], "HIGH", ref)
        for fid in ("FL-131", "FL-132", "FL-133", "FL-134", "FL-135", "FL-136", "FL-137", "FL-138", "FL-139"):
            self.assertIn(fid, self.flagged)

    def test_live_high_set_and_prose(self):
        high = {ref for ref, r in self.events.items() if r["pick"]["confidence"] == "HIGH"}
        self.assertEqual(high, LIVE_HIGH)
        for ref in LIVE_HIGH:
            pk = self.events[ref]["pick"]
            self.assertEqual(pk["release"]["status"], "upcoming", ref)
            self.assertTrue(1.40 <= pk["price"] <= 101.0, ref)
            self.assertGreaterEqual(pk["prob"], 0.55, ref)
            piece = self.preds[ref]
            self.assertEqual(piece["status"], "high", ref)
            self.assertGreaterEqual(len(piece["body"].split()), 30, ref)

    def test_published_prose_never_uses_banned_words(self):
        banned = re.compile(r"\b(model|verified)\b", re.I)
        for ref, p in self.preds.items():
            for field in ("headline", "body", "selection"):
                self.assertIsNone(banned.search(p[field]), f"{ref}.{field}")

    def test_release_clocks_re_observed_on_23_oct(self):
        self.assertEqual(self.rc["checked_at"], "2026-10-23T17:22:00Z")
        ev = self.rc["events"]
        # URC: Irish-time clocks, including the corrected Stormers v Scarlets entry (FL-133)
        for eid, date, time in (("609577", "2026-10-23", "19:45"), ("609579", "2026-10-23", "19:45"),
                                ("609575", "2026-10-23", "19:45"), ("609576", "2026-10-24", "12:45"),
                                ("609580", "2026-10-24", "15:00"), ("609578", "2026-10-24", "18:00")):
            self.assertEqual(ev[eid]["kind"], "exact", eid)
            self.assertEqual(ev[eid]["timezone"], "Irish time", eid)
            self.assertEqual((ev[eid]["date"], ev[eid]["time"]), (date, time), eid)
            self.assertEqual(ev[eid]["checked_at"], "2026-10-23T17:02:00Z", eid)
        # NHL API publishes UTC directly
        self.assertEqual(ev["199984"]["time"], "00:00"); self.assertEqual(ev["199984"]["timezone"], "UTC")
        self.assertEqual(ev["199985"]["time"], "01:00"); self.assertEqual(ev["199985"]["timezone"], "UTC")
        # EuroLeague article prints CEST
        self.assertEqual((ev["535925"]["time"], ev["535925"]["timezone"]), ("20:15", "CEST"))
        self.assertEqual((ev["535926"]["time"], ev["535926"]["timezone"]), ("20:45", "CEST"))
        # 12 NBA games, ET
        nba = [k for k, v in ev.items() if v.get("source") == "https://www.nba.com/schedule?date=2026-10-23"]
        self.assertEqual(len(nba), 12)
        self.assertTrue(all(ev[k]["timezone"] == "ET" and ev[k]["kind"] == "exact" for k in nba))

    def test_unlabelled_clocks_are_never_converted(self):
        ev = self.rc["events"]
        # LNR prints no zone (FL-134): date-only; prior Pro D2 'CET' entries held
        for eid in ("609564", "609567", "609554"):
            self.assertEqual(ev[eid]["kind"], "date_only", eid)
            self.assertIsNone(ev[eid]["timezone"], eid)
        for eid in ("609561", "609562"):
            self.assertTrue(ev[eid].get("hold"), eid)
            self.assertEqual(self.events["RGU-09" if eid == "609561" else "RGU-10"]["pick"]["release"]["status"], "source_conflict")
        # Pages rendering the reader's zone (FL-135) and un-zoned WTA PDFs (FL-097 precedent)
        for eid in ("9951", "9950", "609570", "609573", "609572", "609569", "902157", "3532"):
            self.assertEqual(ev[eid]["kind"], "date_only", eid)
        for eid in ("902162", "902160", "902163"):
            self.assertEqual(ev[eid]["kind"], "not_before", eid)
            self.assertIsNone(ev[eid]["timezone"], eid)
        for ref in ("RGU-12", "RGU-13", "RGU-15", "TEN-56", "SNK-15", "SNK-16"):
            self.assertNotEqual(self.events[ref]["pick"]["confidence"], "HIGH", ref)

    def test_nhl_standings_are_dated_and_archived_rows_keep_their_table(self):
        fd = self.official["form_data"]
        self.assertIn("NHL_standings_2026_10_22", fd)
        self.assertIn("NHL_standings_2026_10_23", fd)
        self.assertEqual(len(fd["NHL_standings_2026_10_23"]["teams"]), 32)
        notes = " ".join(self.events["IHO-30"]["model"]["notes"])
        self.assertIn("standings/2026-10-23", notes)
        old_notes = " ".join(self.events["IHO-15"]["model"]["notes"])  # 22 Oct fixture
        self.assertIn("standings/2026-10-22", old_notes)
        # Montreal is the stronger side on the 23 Oct table but prices just inside -250
        pk = self.events["IHO-30"]["pick"]
        self.assertEqual(pk["label"], "MTL Canadiens")
        self.assertEqual(pk["confidence"], "MEDIUM")
        self.assertFalse(pk["in_band"])

    def test_galway_final_date_move_is_recorded_not_inferred(self):
        gaf = json.loads((DATA / "sports/gaelic_football.json").read_text(encoding="utf-8"))["events"]
        row = next(e for e in gaf if e["ref"] == "GAF-02")
        self.assertEqual(row["start"], "25 Oct 12:00")
        self.assertEqual(row["start_prev"], "24 Oct 14:00")
        conf = self.official["fixture_confirmations"]["GAF-02"]
        self.assertIn("Moved to Sunday", conf["note"])
        self.assertEqual(self.events["GAF-02"]["pick"]["confidence"], "LOW")

    def test_tip_counts_synced_to_23_oct_capture(self):
        self.assertEqual(self.events["BSB-01"]["olbg_tips"], "25/31")
        self.assertEqual(self.events["DRT-09"]["olbg_tips"], "26/31")
        self.assertEqual(self.events["CRK-17"]["olbg_tips"], "4/5")
        self.assertEqual(self.events["BKB-30"]["olbg_pick"], "Valencia")
        self.assertEqual(self.events["RGU-13"]["olbg_market"], "To Win")


if __name__ == "__main__":
    unittest.main()
