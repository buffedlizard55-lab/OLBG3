"""Regression tests for session-1c6981d1.

1. The executive summary is a *merge of the committed rows*, never a second source of truth:
   every pick it publishes must carry a released, in-band, sourced row from one of the two
   pipelines, and the summary must not invent a pick for a row that is not released.
2. The landing page and summary page must actually show the picks and say where they live.
3. The capture-ordering repair (a session-prefixed capture directory silently lost to an older
   one) and the clock-dependent test pins repaired in the same pass.
4. The write-ups added this pass are unique, at least 30 words, and free of the banned wording.
"""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

import exec_summary  # noqa: E402
import live_refresh  # noqa: E402

BANNED = re.compile(r"\b(model|verified|verification)\b", re.I)
PASS_PIECES = ["ICH-200007", "ICH-200001", "ICH-200006", "ICH-200003", "ICH-200008",
               "BKB-536111", "BKB-536112"]


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


class ExecutiveSummaryMerge(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc = exec_summary.build()
        cls.lines = {r["match_id"]: r for r in load("lines.json")}
        cls.matches = {m["id"]: m for m in load("matches.json")}
        cls.events = {r["ref"]: r for r in load("events.json")["events"]}

    def test_every_published_pick_is_released_high_and_in_band(self):
        self.assertTrue(self.doc["picks"], "the summary must publish at least one pick")
        for pick in self.doc["picks"]:
            self.assertEqual(pick["confidence"], "HIGH")
            self.assertTrue(pick["in_band"], pick["match"])
            self.assertTrue(1.40 <= pick["price"] <= 101.0, pick["match"])
            self.assertTrue(pick["start_utc"], pick["match"])
            self.assertTrue(pick["sources"], pick["match"])

    def test_every_pick_maps_back_to_a_released_row(self):
        for pick in self.doc["picks"]:
            key = pick["id"].split("-")[-1]
            row = self.lines.get(pick["tracks"][0]["ref"]) or self.events.get(pick["tracks"][0]["ref"])
            self.assertIsNotNone(row, pick["id"])
            self.assertEqual(row["release"]["status"] if "release" in row else
                             row["pick"]["release"]["status"], "upcoming", pick["id"])

    def test_a_fixture_is_never_listed_twice(self):
        ids = [p["id"] for p in self.doc["picks"]]
        self.assertEqual(len(ids), len(set(ids)))

    def test_no_pick_is_dated_before_the_publication_day(self):
        today = self.doc["today_utc"]
        for pick in self.doc["picks"]:
            self.assertGreaterEqual(pick["start_utc"][:10], today, pick["match"])

    def test_a_released_row_missing_from_the_summary_would_be_a_bug(self):
        """The summary must not silently drop a released HIGH row from either pipeline."""
        covered = {p["id"].split("-")[-1] for p in self.doc["picks"]}
        for mid, row in self.lines.items():
            if row["confidence"] == "high" and (row.get("release") or {}).get("status") == "upcoming":
                self.assertIn(mid.split("-")[-1], covered, mid)


class RenderSurfaces(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The published artifact is site/; the repository root is the legacy publisher's copy.
        # CI refreshes the root snapshot after building, so test whichever exists and require
        # the two to agree when both do (see test_root_snapshot_matches_the_artifact).
        cls.summary_path = (ROOT / "summary.html") if (ROOT / "summary.html").exists() \
            else (ROOT / "site" / "summary.html")
        cls.summary = cls.summary_path.read_text(encoding="utf-8")
        cls.index = (ROOT / "index.html").read_text(encoding="utf-8")
        cls.doc = json.loads((DATA / "exec_summary.json").read_text(encoding="utf-8"))

    def test_both_pages_name_the_selection_column(self):
        for page in (self.summary, self.index):
            self.assertIn("Selection (the pick)", page)
            self.assertIn("summary.html", page)

    def test_every_pick_has_an_anchor_and_a_write_up_section(self):
        self.assertIn('id="writeups"', self.summary)
        for pick in self.doc["picks"]:
            anchor = 'id="pick-%s-%s"' % (pick["slug"], pick["id"].split("-")[-1])
            self.assertIn(anchor, self.summary, pick["match"])

    def test_the_landing_page_carries_the_same_picks_as_the_summary(self):
        for pick in self.doc["today"]:
            self.assertIn(pick["selection"].replace('"', "&quot;")[:20], self.index, pick["match"])

    def test_the_summary_states_the_per_sport_position_for_every_sport(self):
        for sport in exec_summary.SPORTS:
            self.assertIn(sport, self.summary, sport)


class CaptureOrdering(unittest.TestCase):
    def test_a_session_prefixed_capture_sorts_by_its_stamp_not_its_name(self):
        # The defect: "live-1c6981d1-20261024T1710Z" sorts before "live-20261023T1700Z" by name,
        # so a fresh capture was ignored. The stamp is the only ordering key.
        newer = Path("live-1c6981d1-20261024T1710Z")
        older = Path("live-20261023T1700Z")
        self.assertLess(newer.name, older.name)
        self.assertGreater(live_refresh.stamp_of(newer), live_refresh.stamp_of(older))

    def test_the_live_primary_maps_to_a_committed_capture(self):
        pinned = live_refresh.live_primary_capture()
        self.assertIsNotNone(pinned)
        self.assertTrue((ROOT / "data/raw" / pinned / "manifest.json").exists(), pinned)


class AddedWriteUps(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pieces = {p["match_id"]: p for p in load("predictions-olbg.json")["predictions"]}

    def test_each_added_piece_is_written_unique_and_long_enough(self):
        texts = []
        for mid in PASS_PIECES:
            piece = self.pieces[mid]
            words = len(re.findall(r"[A-Za-z0-9'’\-]+", piece["text"]))
            self.assertGreaterEqual(words, 30, mid)
            self.assertEqual(piece["confidence"], "high", mid)
            self.assertTrue(piece["sources"], mid)
            texts.append(piece["text"])
        self.assertEqual(len(texts), len(set(texts)), "write-ups must not be duplicated")

    def test_added_pieces_avoid_the_banned_wording(self):
        for mid in PASS_PIECES:
            self.assertIsNone(BANNED.search(self.pieces[mid]["text"]), mid)

    def test_each_added_piece_names_its_own_fixture(self):
        for mid, piece in self.pieces.items():
            if mid not in PASS_PIECES:
                continue
            self.assertEqual(piece["match_id"], mid)
            self.assertIn(piece["sport"], ("Ice Hockey", "Basketball"))

    def test_added_pieces_cite_the_league_itself(self):
        for mid in PASS_PIECES:
            hosts = {s["url"].split("/")[2] for s in self.pieces[mid]["sources"]}
            self.assertTrue(hosts <= {"api-web.nhle.com", "www.nba.com"}, hosts)


class SummaryGate(unittest.TestCase):
    def test_the_summary_checker_passes_on_the_committed_data(self):
        import subprocess
        result = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_exec_summary.py")],
                                capture_output=True, text=True, cwd=str(ROOT))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS:", result.stdout)

    def test_the_checker_rejects_a_pick_that_no_longer_passes_the_band(self):
        """A guard that only ever sees good data proves nothing; drive it with a bad one."""
        import subprocess, tempfile, shutil
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            for name in ("exec_summary.json", "lines.json", "predictions.json",
                         "predictions-olbg.json", "matches.json"):
                shutil.copyfile(DATA / name, tmp / name)
            doc = json.loads((tmp / "exec_summary.json").read_text())
            if not doc["picks"]:
                self.skipTest("no picks to corrupt")
            doc["picks"][0]["price"] = 1.01
            (tmp / "exec_summary.json").write_text(json.dumps(doc))
            src = (ROOT / "scripts" / "check_exec_summary.py").read_text()
            src = src.replace('DATA = ROOT / "data"', 'DATA = Path(%r)' % str(tmp))
            src = src.replace('ROOT = Path(__file__).resolve().parents[1]',
                              'ROOT = Path(%r)' % str(ROOT))
            script = tmp / "check.py"
            script.write_text(src)
            result = subprocess.run([sys.executable, str(script)], capture_output=True,
                                    text=True, cwd=str(ROOT))
            self.assertEqual(result.returncode, 1, result.stdout)
            self.assertIn("outside", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
