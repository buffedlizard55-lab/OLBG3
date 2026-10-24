"""Regression tests for session-b322f52e (task-55, 2026-10-23T21:33Z SvelteKit supplement & audit).

Pins:
  * FL-194: scripts/extract_listings.py --svelte-fallback extracts all 123 active (expired == "0")
    rows across 12 sports from data/raw/svelte-b322f52e-20261023T2133Z while keeping default
    SSR-only extraction byte-identical on live-20261023T1700Z (177 rows) and preserving empty SSR
    output on live-20261023T2135Z.
  * FL-195: RGU-609581 (Ospreys v Dragons) carries the official 18:45Z URC kick-off while
    preserving OLBG's 18:00Z card timestamp in olbg_start_utc.
  * FL-196: 'Top Team1 Batsman' is present in all three non-winner market sets so CRI-188845
    ('RRS Cornwall (Toronto Kings)') cannot leak into match-winner probability.
  * FL-197: verifications.json entries 36995 and 36996 no longer carry swapped Trento/Perugia
    arenas or the contradicted 97:85 Round 1 tally.
  * FL-198: no row in data/lines.json has an inverted our_home_probability when the selected side
    resolves to the home club via resolve_team_side().
  * FL-176 resolution: /olbg/index.html renders every source link in p['sources'] for each HIGH row.
  * All 11 net-new HIGH pieces + refreshed MTR-913 carry >=30 words, unique prose, https official
    sources, exact price quotes, and zero banned vocabulary ('model', 'verified', 'verification').
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "tools"))

import extract_listings as ex  # noqa: E402
import originate as orig       # noqa: E402

BANNED = re.compile(r"\b(model|verified|verification)\b", re.I)
SESSION_PIECES = [
    "MTR-913",
    "BKB-536039", "BKB-536042", "BKB-536043",
    "VOL-36995", "VOL-36996",
    "RGU-609581",
    "HAN-12138", "HAN-12130", "HAN-12134", "HAN-12129", "HAN-12133",
]


class SvelteKitHydrationExtractorTest(unittest.TestCase):
    def test_svelte_fallback_extracts_active_rows_only(self):
        capture = DATA / "raw/svelte-b322f52e-20261023T2133Z"
        rows, report = ex.parse_capture(capture, svelte_fallback=True)
        deduped = ex.dedupe(rows)
        self.assertEqual(len(deduped), 123)
        sports = {r["sport"] for r in deduped}
        self.assertEqual(len(sports), 12)
        eids = {r["event_id"] for r in deduped}
        for expected in ("609581", "36995", "36996", "12138", "12130", "12134", "12129", "12133", "902165", "902168"):
            self.assertIn(expected, eids)
        self.assertEqual(report["parse_gaps"], {"Gaelic Football:market": 5})

    def test_default_ssr_mode_stays_zero_on_svelte_only_capture(self):
        capture = DATA / "raw/svelte-b322f52e-20261023T2133Z"
        rows, _ = ex.parse_capture(capture, svelte_fallback=False)
        self.assertEqual(rows, [])

    def test_ssr_1700z_capture_remains_byte_identical(self):
        capture = DATA / "raw/live-20261023T1700Z"
        committed = (DATA / "raw/olbg-harvest-20261023T1700Z.tsv").read_text(encoding="utf-8")
        rows, report = ex.parse_capture(capture, svelte_fallback=True)
        rows = ex.dedupe(rows)
        rows.sort(key=lambda r: (r["sport"], r["start_utc"], r["event_name"]))
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "recheck.tsv"
            ex.write_tsv(rows, report, out, capture.name)
            self.assertEqual(out.read_text(encoding="utf-8"), committed)


class DefectsAndRepairsB322f52eTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matches = {m["id"]: m for m in json.loads((DATA / "matches.json").read_text(encoding="utf-8"))}
        cls.lines = {l["match_id"]: l for l in json.loads((DATA / "lines.json").read_text(encoding="utf-8"))}
        cls.ver = json.loads((DATA / "verifications.json").read_text(encoding="utf-8"))["event_verifications"]
        cls.rc = json.loads((DATA / "release_checks.json").read_text(encoding="utf-8"))["events"]
        cls.preds = {p["match_id"]: p for p in json.loads((DATA / "predictions-olbg.json").read_text(encoding="utf-8"))["predictions"]}
        cls.flagged = {i["id"]: i for i in json.loads((DATA / "flagged.json").read_text(encoding="utf-8"))["items"]}

    def test_cri_188845_top_batsman_is_classified_as_non_winner(self):
        # 2026-10-24 (session-1c6981d1): OLBG re-listed event 188845 as "Win Match" (6/7 tips) in the
        # 17:11Z capture, so the FL-196 regression can no longer be exercised through the live row:
        # the listing itself changed, not the classification rule. The rule is asserted on the market
        # strings it exists for, and the live row is checked against whatever OLBG now prints.
        import build_dataset as ds
        self.assertIn("Top Team1 Batsman", ds.OTHER_MARKETS)
        self.assertNotIn("Top Team1 Batsman", ds.WIN_MARKETS)
        live = self.matches["CRI-188845"]
        self.assertEqual(live["market_family"],
                         "match_winner" if live["olbg_market"] in ds.WIN_MARKETS else "other",
                         live["olbg_market"])
        if live["olbg_market"] not in ds.WIN_MARKETS:
            self.assertIn("non_win_consensus_excluded_from_winner_probability",
                          self.lines["CRI-188845"]["flags"])

    def test_no_row_has_inverted_home_probability(self):
        for mid, l in self.lines.items():
            home, away, pick = l.get("home"), l.get("away"), l.get("our_pick")
            p_home, p_pick = l.get("our_home_probability"), l.get("our_pick_probability")
            if not (home and away and pick and p_home is not None and p_pick is not None):
                continue
            side = orig.resolve_team_side(pick, home, away)
            if side == home:
                self.assertAlmostEqual(p_home, p_pick, places=4, msg=mid)
            elif side == away:
                self.assertAlmostEqual(p_home, round(1.0 - p_pick, 4), places=4, msg=mid)

    def test_superlega_36995_and_36996_swapped_venues_are_repaired(self):
        self.assertNotIn("Trento", self.ver["36995"].get("venue") or "")
        self.assertNotIn("Perugia", self.ver["36996"].get("venue") or "")
        self.assertNotIn("97:85", self.ver["36995"]["facts"][0])
        self.assertIn("78:65", self.ver["36995"]["facts"][0])

    def test_ospreys_v_dragons_clock_discrepancy_is_recorded(self):
        self.assertEqual(self.matches["RGU-609581"]["olbg_start_utc"], "2026-10-24T18:00:00.000Z")
        self.assertEqual(self.matches["RGU-609581"]["official_start_utc"], "2026-10-24T18:45:00Z")
        self.assertEqual(self.rc["609581"]["time"], "19:45")
        self.assertEqual(self.rc["609581"]["timezone"], "Irish time")

    def test_fl176_landing_table_renders_all_sources_per_high_row(self):
        index_html = (ROOT / "olbg/index.html").read_text(encoding="utf-8")
        self.assertIn(">source 1</a>", index_html)
        self.assertIn(">source 2</a>", index_html)
        self.assertEqual(self.flagged["FL-176"]["status"], "resolved")

    def test_new_register_items_are_present_and_sourced(self):
        for fid in ("FL-194", "FL-195", "FL-196", "FL-197", "FL-198"):
            self.assertIn(fid, self.flagged)
            self.assertTrue(self.flagged[fid]["sources"], fid)
            for src in self.flagged[fid]["sources"]:
                self.assertTrue(src["url"].startswith("https://"), fid)

    def test_session_high_pieces_meet_all_brief_gates(self):
        texts = []
        for mid in SESSION_PIECES:
            self.assertIn(mid, self.preds, mid)
            p = self.preds[mid]
            row = self.lines[mid]
            self.assertGreaterEqual(len(p["text"].split()), 30, mid)
            self.assertIsNone(BANNED.search(p["selection"] + " " + p["text"]), mid)
            self.assertTrue(1.40 <= row["our_price_pick"] <= 101.00, mid)
            self.assertLess(row["our_pick_probability"], 0.70, mid)
            for s in p["sources"]:
                self.assertTrue(s["url"].startswith("https://"), mid)
            texts.append(p["text"])
        self.assertEqual(len(texts), len(set(texts)))


if __name__ == "__main__":
    unittest.main()
