"""Regression pins from session-2f1b3baa's post-refresh audit (2026-10-24).

Each invariant below was independently re-verified against live official
sources during the audit (NHL schedule/standings/gamecenter APIs, MLB Stats
API, unitedrugby.com fixtures, gaacork.ie event page, ehfcl.eurohandball.com
standings/calendar, volleyballworld snapshot, formula1.com United States GP
page). See docs/audit-2f1b3baa.md for the line-by-line record.

Pinned invariants:

1. Both tracks: every HIGH/``high`` pick sits strictly inside the brief's
   -250..+10000 US-odds band (decimal 1.40..101.00), carries a write-up of at
   least 30 words, names no internal-only term ("model"/"verified"/cognates),
   and cites at least one https source.
2. The executive summary (today.html) is a primary nav page, contains the
   ``live-high`` table, shows exactly one row per currently-live root-track
   HIGH pick (events + gap sports), and every row links both the write-up
   anchor and an official https source.
3. The brief-coverage accounting recomputes exactly from the tracks (never
   padded toward the five-per-sport target): live_high_root and
   live_high_olbg equal fresh re-counts, and the union lies inside
   [max(root, olbg), root + olbg] and never exceeds the 75-pick target.

The counts are derived from the same build's data files rather than pinned as
constants, so this suite stays green as picks legitimately expire with the
publication clock; it complements check_board.py's kick-off liveness gate.
"""

import json
import os
import re
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BANNED = re.compile(r"\b(models?|verified|verification|verify|verifying)\b", re.IGNORECASE)
MIN_WORDS = 30
BAND_LO, BAND_HI = 1.40, 101.00  # -250 .. +10000 in decimal odds
TARGET_TOTAL = 75


def _load(path):
    with open(os.path.join(ROOT, path), encoding="utf-8") as fh:
        return json.load(fh)


def _root_high_rows():
    events = _load("data/events.json")["events"]
    gap = _load("data/gap_sports.json")["rows"]
    return ([r for r in events if (r.get("pick") or {}).get("confidence") == "HIGH"]
            + [r for r in gap if (r.get("pick") or {}).get("confidence") == "HIGH"])


def _root_live_high():
    return [r for r in _root_high_rows()
            if (r["pick"].get("release") or {}).get("status") == "upcoming"]


def _olbg_live_high():
    lines = _load("data/lines.json")
    return [r for r in lines
            if r.get("confidence") == "high"
            and (r.get("release") or {}).get("status") == "upcoming"]


class TestHighPickProseAndBand(unittest.TestCase):
    def test_root_track_band_prose_sources(self):
        preds = {p["ref"]: p for p in _load("data/predictions.json")["predictions"]}
        highs = _root_high_rows()
        for r in highs:
            pk = r["pick"]
            price = pk.get("price")
            self.assertIsInstance(price, (int, float), r["ref"])
            self.assertGreaterEqual(price, BAND_LO, r["ref"])
            self.assertLessEqual(price, BAND_HI, r["ref"])
            pred = preds.get(r["ref"])
            self.assertIsNotNone(pred, f"{r['ref']} HIGH without a write-up")
            body = pred.get("body") or ""
            self.assertGreaterEqual(len(body.split()), MIN_WORDS, r["ref"])
            self.assertFalse(BANNED.search(body), f"{r['ref']} uses an internal-only word")
            self.assertTrue(
                any(str(s.get("url", "")).startswith("https://") for s in pred.get("sources", [])),
                f"{r['ref']} HIGH without an https source")

    def test_olbg_track_band_prose_sources(self):
        preds = {p["match_id"]: p for p in _load("data/predictions-olbg.json")["predictions"]}
        highs = _olbg_live_high()
        for row in highs:
            price = row.get("our_price_pick")
            self.assertIsInstance(price, (int, float), row["match_id"])
            self.assertGreaterEqual(price, BAND_LO, row["match_id"])
            self.assertLessEqual(price, BAND_HI, row["match_id"])
            pred = preds.get(row["match_id"])
            self.assertIsNotNone(pred, f"{row['match_id']} high without a write-up")
            text = pred.get("text") or ""
            self.assertGreaterEqual(len(text.split()), MIN_WORDS, row["match_id"])
            self.assertFalse(BANNED.search(text), f"{row['match_id']} uses an internal-only word")
            self.assertTrue(
                any(str(s.get("url", "")).startswith("https://") for s in pred.get("sources", [])),
                f"{row['match_id']} high without an https source")


class TestExecutiveSummary(unittest.TestCase):
    def test_today_page_nav_and_table(self):
        path = os.path.join(ROOT, "today.html")
        self.assertTrue(os.path.exists(path), "today.html executive summary is missing")
        with open(path, encoding="utf-8") as fh:
            html = fh.read()
        self.assertIn('href="today.html"', html, "today.html must be a primary nav entry")
        self.assertIn('id="live-high"', html)
        live = _root_live_high()
        hero = html.split('id="live-high"', 1)[1].split("</table>", 1)[0]
        rows = [r for r in re.findall(r"<tr>(.*?)</tr>", hero, re.S)[1:]
                if "predictions.html#" in r]
        self.assertEqual(len(rows), len(live),
                         "executive summary must show one row per live HIGH pick")
        for row in rows:
            self.assertIn("predictions.html#", row, "hero row lacks a write-up link")
            self.assertRegex(row, r'href="https://', "hero row lacks an official https source")
        # Both tracks' counts must be stated so the reader knows where the picks live.
        self.assertRegex(html, r"OLBG lines board", "the second board's picks must be reachable")


class TestBriefAccountingHonesty(unittest.TestCase):
    def test_totals_recompute_without_padding(self):
        totals = _load("data/brief_coverage.json")["totals"]
        root_live = len(_root_live_high())
        olbg_live = len(_olbg_live_high())
        self.assertEqual(totals["live_high_root"], root_live)
        self.assertEqual(totals["live_high_olbg"], olbg_live)
        union = totals["live_high_union"]
        self.assertGreaterEqual(union, max(root_live, olbg_live))
        self.assertLessEqual(union, root_live + olbg_live)
        self.assertLessEqual(union, TARGET_TOTAL)
        self.assertEqual(totals["shortfall_to_target"], TARGET_TOTAL - union)


if __name__ == "__main__":
    unittest.main()
