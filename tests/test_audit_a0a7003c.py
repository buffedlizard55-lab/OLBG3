import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

EXCLUDED = {
    "soccer", "football", "boxing", "ufc", "mma",
    "american_football", "american football", "hurling",
    "horse_racing", "horse racing", "cycling", "specials",
}


class AuditA0a7003cTests(unittest.TestCase):
    def test_harvest_tsv_schema_and_exclusions(self):
        tsv = ROOT / "docs/harvest-20261022-1215z.tsv"
        self.assertTrue(tsv.exists())
        rows = [
            line.split("|")
            for line in tsv.read_text(encoding="utf-8").splitlines()
            if line and not line.startswith("#")
        ]
        self.assertGreaterEqual(len(rows), 150)
        seen_ids = set()
        for parts in rows:
            self.assertEqual(len(parts), 11, f"Expected 11 columns in {parts}")
            sport, _lg, prefix, slug, eid = parts[:5]
            self.assertNotIn(sport.lower(), EXCLUDED)
            root_seg = prefix.split("/")[0]
            for ex in ("Football", "Horse_Racing", "Boxing", "UFC", "MMA", "American_Football", "Hurling", "Cycling", "Specials"):
                self.assertNotEqual(root_seg, ex)
            self.assertTrue(eid.isdigit(), f"Non-numeric event_id {eid!r}")
            self.assertTrue(slug)
            self.assertNotIn(eid, seen_ids, f"Duplicate event_id {eid}")
            seen_ids.add(eid)
        for nhl_eid in ("199931", "199932", "199933", "199934", "199935", "199936",
                        "199937", "199938", "199939", "199940", "199941", "199942"):
            self.assertIn(nhl_eid, seen_ids)
        for new_eid in ("902135", "902134", "188830", "37005"):
            self.assertIn(new_eid, seen_ids)

    def test_verifications_json_nhl_and_lnv_invariants(self):
        vpath = ROOT / "docs/verifications-a0a7003c.json"
        self.assertTrue(vpath.exists())
        doc = json.loads(vpath.read_text(encoding="utf-8"))
        teams = doc["nhl_2026_10_22"]["teams"]
        self.assertEqual(len(teams), 32)
        for abbrev, t in teams.items():
            self.assertEqual(t["w"] + t["l"] + t["ot"], t["gp"], f"{abbrev} GP mismatch")
            self.assertEqual(2 * t["w"] + t["ot"], t["pts"], f"{abbrev} PTS mismatch")
        clubs = doc["lnv_alterna_volstar_j2"]["clubs"]
        self.assertEqual(len(clubs), 14)
        for cname, c in clubs.items():
            self.assertEqual(c["w"] + c["l"], c["p"], f"{cname} played mismatch")
        fix = doc["model_and_url_corrections"]["ICH-199937_home_ice_sign_fix"]
        self.assertAlmostEqual(fix["corrected_prob"], 0.5306, places=4)
        self.assertEqual(fix["corrected_confidence"], "medium")
        self.assertEqual(len(doc["olbg_track_27_upgrades"]), 27)

    def test_phase2_integrated_board_and_fixes(self):
        events = {r["ref"]: r for r in json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]}
        gap = {r["ref"]: r for r in json.loads((DATA / "gap_sports.json").read_text(encoding="utf-8"))["rows"]}
        matches = {r["id"]: r for r in json.loads((DATA / "matches.json").read_text(encoding="utf-8"))}
        lines = {r["match_id"]: r for r in json.loads((DATA / "lines.json").read_text(encoding="utf-8"))}
        preds_root = {p["ref"]: p for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]}
        preds_olbg = {p["match_id"]: p for p in json.loads((DATA / "predictions-olbg.json").read_text(encoding="utf-8"))["predictions"]}
        vdoc = json.loads((ROOT / "docs/verifications-a0a7003c.json").read_text(encoding="utf-8"))

        # 1. ICH-199937 road home-ice sign bug fixed and aligned with IHO-14
        self.assertEqual(lines["ICH-199937"]["confidence"], "medium")
        self.assertAlmostEqual(lines["ICH-199937"]["our_pick_probability"], 0.5306, places=4)
        self.assertEqual(lines["ICH-199937"]["our_price_pick"], 1.79)
        self.assertEqual(preds_olbg["ICH-199937"]["status"], "analysis")
        self.assertEqual(events["IHO-14"]["pick"]["confidence"], "MEDIUM")
        self.assertEqual(events["IHO-14"]["pick"]["price"], 1.79)

        # 2. All 5 new midday NHL in-band HIGH picks active on both tracks;
        #    VOL-30 / VOL-37005 is MEDIUM / analysis per FL-096 because official lnv.fr prints '(20h)' with no CEST label.
        expected_pairs = [
            ("IHO-15", "ICH-199931", "EDM Oilers", 1.69),
            ("IHO-16", "ICH-199932", "NJ Devils", 1.68),
            ("IHO-17", "ICH-199933", "DET Red Wings", 1.59),
            ("IHO-23", "ICH-199940", "VGS Golden Knights", 1.53),
            ("IHO-24", "ICH-199941", "DAL Stars", 1.42),
        ]
        for rref, omid, label, dec_price in expected_pairs:
            self.assertEqual(events[rref]["pick"]["confidence"], "HIGH", rref)
            self.assertEqual(events[rref]["pick"]["label"], label, rref)
            self.assertEqual(events[rref]["pick"]["price"], dec_price, rref)
            self.assertGreaterEqual(len(preds_root[rref]["body"].split()), 30, rref)
            self.assertEqual(lines[omid]["confidence"], "high", omid)
            self.assertEqual(lines[omid]["our_pick"], label, omid)
            self.assertEqual(lines[omid]["our_price_pick"], dec_price, omid)
            self.assertGreaterEqual(len(preds_olbg[omid]["text"].split()), 30, omid)
        self.assertEqual(events["VOL-30"]["pick"]["confidence"], "MEDIUM")
        self.assertEqual(events["VOL-30"]["pick"]["label"], "Chaumont")
        # Evening refresh 2026-10-22T20:55Z (session-784afe97): the Sete v Chaumont tie has
        # rotated off the live OLBG listing, so the row is now carried from the dated 12:15Z
        # capture and can no longer carry a live grade. It stays published as analysis.
        self.assertEqual(lines["VOL-37005"]["confidence"], "low")
        self.assertEqual(preds_olbg["VOL-37005"]["status"], "analysis")

        # 3. Man Of The Match non-winner market guard on CRK-11 / CRI-188830
        self.assertEqual(events["CRK-11"]["model"]["basis"], "none")
        self.assertEqual(events["CRK-11"]["model"]["prices"], {})
        self.assertIn("non_win_consensus_excluded_from_winner_probability", lines["CRI-188830"]["flags"])

        # 4. All 27 cross-synced /olbg/ rows verified and Stifel Charity Classic live override applied
        for mid in vdoc["olbg_track_27_upgrades"]:
            self.assertEqual(matches[mid]["competition_status"], "verified", mid)
        self.assertEqual(gap["GLF-05"]["pick"]["label"], "Stewart Cink")
        self.assertEqual(gap["GLF-05"]["olbg_tips"], "3/13")
        self.assertEqual(gap["GLF-07"]["pick"]["release"]["status"], "start_window_reached")


if __name__ == "__main__":
    unittest.main()
