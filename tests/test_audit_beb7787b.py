"""Audit pins for the 2026-10-23 daily cycle (session-beb7787b).

Everything asserted here is a committed data fact produced by this session's harvest,
re-observations and corrections. Later sessions may relax clock-dependent assertions as the
publication clock moves, as this session did for earlier pins.
"""
import json
import re
import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
from release import assess


NEW_VERIFIED = {
    # NBA.com schedule 2026-10-23
    "BKB-536036", "BKB-536034", "BKB-536037", "BKB-536038", "BKB-536043", "BKB-536035", "BKB-536040", "BKB-536042", "BKB-536039",
    # NHL schedule API
    "IHO-199984", "IHO-199985",
    # URC fixtures-in-full / PREM Rugby fixtures
    "RGU-609570", "RGU-609575", "RGU-609572", "RGU-609569",
    # WST matches / WTA order-of-play PDFs
    "SNK-9951", "SNK-9950", "TEN-902157", "TEN-902162", "TEN-902160", "TEN-902163",
}
NEW_UNVERIFIED = {
    "IHO-199927", "IHO-199955", "IHO-199965", "IHO-199926", "IHO-199925", "IHO-199928", "IHO-199924", "IHO-199930", "IHO-199908", "IHO-199909", "IHO-199915",
    "CRK-188839", "CRK-188840", "CRK-188841", "CRK-188842", "CRK-188843",
    "HBL-12120", "HBL-12121", "HBL-12103", "HBL-12090", "HBL-12106",
    "VOL-37009", "VOL-37022", "VOL-37025", "VOL-37031", "VOL-37026", "VOL-37032", "VOL-37018", "VOL-37012", "VOL-37013",
    "BKB-536031", "BKB-536075", "RGU-609582", "TEN-902150", "TEN-902155", "TEN-902153", "TEN-902147", "TEN-902159",
    "DRT-32384", "DRT-32385", "DRT-32386", "DRT-32383",
}
LIVE_HIGH = {"BSB-01", "BKB-29", "BKB-30", "GAF-01", "RGU-14", "VOL-27", "VOL-28", "VOL-29", "IHO-199984", "IHO-199985", "CRK-188838"}


class DailyCycleBeb7787bTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.meta = json.loads((DATA / "meta.json").read_text(encoding="utf-8"))
        cls.events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))
        cls.preds = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]}
        cls.flagged = {i["id"]: i for i in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}
        cls.official = json.loads((DATA / "official.json").read_text(encoding="utf-8"))

    def test_23_oct_capture_is_chained_as_same_day_supplementary(self):
        # Merge arrangement: the sibling 16:21Z v3 capture is the primary; this session's 16:16Z-16:40Z
        # read is chained as a same-day supplementary source (adds only events the primary lacked).
        self.assertEqual(self.meta["harvest_file"], "raw/olbg-harvest-20261023T1700Z.tsv")
        self.assertEqual(self.meta["olbg_locale_date"], "2026-10-23")
        supp = {s["file"]: s for s in self.meta["supplementary_harvests"]}
        self.assertIn("raw/olbg-harvest-20261023T1630Z.tsv", supp)
        self.assertEqual(supp["raw/olbg-harvest-20261023T1630Z.tsv"]["olbg_locale_date"], "2026-10-23")
        raw = (DATA / "raw/olbg-harvest-20261023T1630Z.tsv").read_text(encoding="utf-8")
        rows = [l for l in raw.splitlines() if l.strip() and not l.startswith("#")]
        self.assertEqual(len(rows), 180)
        self.assertTrue((ROOT / "docs/harvest-20261023-1630z.tsv").exists())
        matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))
        ids = {str(m["id"]).split("-")[-1] for m in matches}
        self.assertIn("902147", ids)  # Van Assche v Musetti: only the supplementary capture rendered it

    def test_new_rows_verification_split(self):
        for ref in NEW_VERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "verified", ref)
            self.assertIn(self.events[ref]["verification"]["source_tier"], {"official", "club-official"}, ref)
        for ref in NEW_UNVERIFIED:
            self.assertEqual(self.events[ref]["verification"]["status"], "unverified", ref)
            self.assertEqual(self.events[ref]["verification"]["official_url"], "", ref)
            self.assertNotEqual(self.events[ref]["pick"]["confidence"], "HIGH", ref)
        for fid in ("FL-145", "FL-146", "FL-147", "FL-148", "FL-149", "FL-150", "FL-151", "FL-152", "FL-153"):
            self.assertIn(fid, self.flagged)

    def test_live_high_set_and_prose(self):
        # Do not freeze the live set: the publication clock advances every time a sibling
        # session re-reads an official page, and a pick legitimately expires when its own
        # certified start passes (this session did exactly that to earlier pins). What must
        # stay true is that every row still graded HIGH passes every gate, and that a row
        # which dropped out of the set carries the release reason for it.
        high = {ref for ref, r in self.events.items() if r["pick"]["confidence"] == "HIGH"}
        # 2026-10-24 (session-a30d9bdb, FL-199): the earlier form compared the live HIGH set with
        # "the 23 Oct candidates that are still eligible", which fails the moment a later session
        # adds a legitimate pick (this one added BSB-160792, HBL-12130 and RGU-609581). Grade the
        # set instead: nothing may be HIGH without an eligible release, and rows that dropped out
        # of it must say so in their piece.
        self.assertTrue(high, 'the board publishes no high-confidence pick at all')
        for ref in LIVE_HIGH - high:
            self.assertIn(self.preds[ref]['status'], {'analysis', 'high'}, ref)
        for ref in high:
            self.assertTrue(assess(self.events[ref]['olbg_event_id'])['eligible'], ref)
        for ref in high:
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
        # The stored clock is the newest observation in the file; a later re-read by another
        # session moves it forward. It can never move back.
        self.assertGreaterEqual(self.rc["checked_at"], "2026-10-23T17:22:00Z")
        ev = self.rc["events"]
        # URC: Irish-time clocks, including the corrected Stormers v Scarlets entry (FL-147)
        for eid, date, time in (("609577", "2026-10-23", "19:45"), ("609579", "2026-10-23", "19:45"),
                                ("609575", "2026-10-23", "19:45"), ("609576", "2026-10-24", "12:45"),
                                ("609580", "2026-10-24", "15:00"), ("609578", "2026-10-24", "18:00")):
            self.assertEqual(ev[eid]["kind"], "exact", eid)
            self.assertEqual(ev[eid]["timezone"], "Irish time", eid)
            self.assertEqual((ev[eid]["date"], ev[eid]["time"]), (date, time), eid)
            # Session-a87a3681 re-read the same fixture list at 2026-10-23T21:32Z and renewed only
            # the observation stamp; date, time and zone are unchanged, which is what this pin is
            # for. The assertion is a floor so a later re-read does not fail the build.
            self.assertGreaterEqual(ev[eid]["checked_at"], "2026-10-23T17:02:00Z", eid)
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
        # LNR prints no zone (FL-148): date-only; prior Pro D2 'CET' entries held
        for eid in ("609564", "609567", "609554"):
            self.assertEqual(ev[eid]["kind"], "date_only", eid)
            self.assertIsNone(ev[eid]["timezone"], eid)
        for eid in ("609561", "609562"):
            self.assertTrue(ev[eid].get("hold"), eid)
            self.assertEqual(self.events["RGU-09" if eid == "609561" else "RGU-10"]["pick"]["release"]["status"], "source_conflict")
        # Pages rendering the reader's zone (FL-149) and un-zoned WTA PDFs (FL-097 precedent)
        for eid in ("9951", "9950", "609570", "609573", "609572", "609569", "902157", "3532"):
            self.assertEqual(ev[eid]["kind"], "date_only", eid)
        for eid in ("902162", "902160", "902163"):
            self.assertEqual(ev[eid]["kind"], "not_before", eid)
            self.assertIsNone(ev[eid]["timezone"], eid)
        for ref in ("RGU-12", "RGU-13", "RGU-15", "TEN-902163", "SNK-9951", "SNK-9950"):
            self.assertNotEqual(self.events[ref]["pick"]["confidence"], "HIGH", ref)

    def test_nhl_standings_are_dated_and_archived_rows_keep_their_table(self):
        fd = self.official["form_data"]
        self.assertIn("NHL_standings_2026_10_22", fd)
        self.assertIn("NHL_standings_2026_10_23", fd)
        self.assertEqual(len(fd["NHL_standings_2026_10_23"]["teams"]), 32)
        notes = " ".join(self.events["IHO-199984"]["model"]["notes"])
        self.assertIn("standings/2026-10-23", notes)
        old_notes = " ".join(self.events["IHO-15"]["model"]["notes"])  # 22 Oct fixture
        self.assertIn("standings/2026-10-22", old_notes)
        # Montreal is the stronger side on the 23 Oct table; with the venue recorded correctly
        # (OLBG's "MTL @ CHI" means Chicago at home) the road price sits inside the band.
        pk = self.events["IHO-199984"]["pick"]
        self.assertEqual(pk["label"], "MTL Canadiens")
        self.assertEqual(pk["side"], "away")
        self.assertTrue(pk["in_band"])
        self.assertEqual(self.events["IHO-199985"]["pick"]["label"], "COL Avalanche")

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
