import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent

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
        # All 12 Thu Oct 22 NHL games must be present in the midday harvest
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


if __name__ == "__main__":
    unittest.main()
