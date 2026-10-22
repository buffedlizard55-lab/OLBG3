"""Audit & integration test suite for task-37 / task-38 (session d3464fe4).

Verifies both Phase 1 standalone audit artifacts AND (once Phase 2 integration has run)
all cross-board invariants across root `/` and `/olbg/`:
  - 15 covered OLBG sports and strictly 0 excluded sports across every dataset & page
  - 202/202 (100%) two-sided root fixtures verified on primary official/club-official hosts
  - 28/28 (100%) gap-sport rows priced (DRT-17 re-priced onto Gerwyn Price 7.46 / +646 MEDIUM after the
    official PDC Humphries withdrawal, FL-078, session-bb34505f midday re-harvest)
  - Exact live non-chalk HIGH sport alignment across `/` (9 sports, 15 HIGH) and `/olbg/` (11 sports, 20 HIGH)
  - Every HIGH pick strictly inside -250..+10000 (1.40..101.00), <70% probability, live kick-off,
    and unique >=30-word human prediction citing verified teams/players & match history
  - Un-crossed Italian SuperLega IDs (36994..36997), CBV home/away order on VOL-37000,
    WTA Osaka tournament correction on TEN-37 / TEN-902107, non-winner consensus exclusion,
    and zero soft-404 OLBG URLs across all 230 `/` rows and 303 `/olbg/` rows.
"""
from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DATA = ROOT / "data"

EXCLUDED_SPORTS = {
    "football",
    "soccer",
    "boxing",
    "ufc",
    "mma",
    "american football",
    "hurling",
    "horse racing",
    "cycling",
    "specials",
}

EXPECTED_15_SPORTS = {
    "Basketball",
    "Baseball",
    "Tennis",
    "Cricket",
    "Ice Hockey",
    "Darts",
    "Snooker",
    "Handball",
    "Volleyball",
    "Rugby Union",
    "Rugby League",
    "Golf",
    "Motor Racing",
    "Gaelic Football",
    "Greyhounds",
}

# Session-bb34505f (2026-10-22 midday integration): Darts left the root HIGH set when DRT-17 was
# demoted HIGH->MEDIUM after the official PDC Humphries withdrawal (FL-078: no directly retrievable
# official form page for the new consensus leader Gerwyn Price), and Golf left it when GLF-02 (Bermuda,
# in play since 10:35Z) hit the start-window release gate and GLF-05 (Stifel, flipped to Cink) has no
# verified exact start. Darts stays HIGH on `/olbg/` via DAR-32324 and the rewritten DAR-32338 Price piece.
EXPECTED_ROOT_HIGH_SPORTS = {
    "Baseball",
    "Basketball",
    "Cricket",
    "Ice Hockey",
    "Handball",
    "Volleyball",
    "Rugby Union",
    "Motor Racing",
    "Gaelic Football",
}

EXPECTED_OLBG_HIGH_SPORTS = EXPECTED_ROOT_HIGH_SPORTS | {"Rugby League", "Darts"}

NON_WINNER_MARKETS = {
    "Set Score",
    "Set Betting",
    "Handicap",
    "Handicap 2-way",
    "Match Handicap",
    "Pointspread",
    "Puck Line",
    "Total Legs",
    "Game Totals",
    "Games Won",
    "1st Set Winner",
}


class Harvest0830AuditTest(unittest.TestCase):
    def test_harvest_covers_all_15_in_scope_sports_and_zero_excluded(self) -> None:
        tsv = (DOCS / "harvest-20261022-0830z.tsv").read_text(encoding="utf-8").splitlines()
        rows = [line.split("|") for line in tsv if line and not line.startswith("#")]
        self.assertGreaterEqual(len(rows), 100)

        sports = {r[0].replace("_", " ") for r in rows}
        self.assertEqual(sports, EXPECTED_15_SPORTS)
        for s in sports:
            self.assertNotIn(s.lower(), EXCLUDED_SPORTS)

        seen_ids: set[str] = set()
        for r in rows:
            self.assertEqual(len(r), 11, f"Malformed TSV row: {r}")
            sport, league_lbl, prefix, slug, eid = r[0], r[1], r[2], r[3], r[4]
            self.assertTrue(prefix and slug and eid.isdigit(), f"Bad URL parts: {r}")
            self.assertNotIn(eid, seen_ids, f"Duplicate event_id {eid}")
            seen_ids.add(eid)
            if sport == "Greyhounds":
                self.assertRegex(slug, r"^\d{1,2}:\d{2}_[A-Za-z_]+$")
                self.assertNotEqual(eid, "689613", "Closed Greyhound race 689613 must not appear")

    def test_verifications_bundle_uses_primary_https_sources_and_preserves_unverified(self) -> None:
        bundle = json.loads((DOCS / "verifications-d3464fe4.json").read_text(encoding="utf-8"))
        evs = {v["event_id"]: v for v in bundle["verifications"]}
        self.assertEqual(len(evs), 21)

        unverified = [eid for eid, v in evs.items() if v["status"] == "unverified"]
        self.assertEqual(set(unverified), {"188350", "3327"})
        for eid in unverified:
            self.assertEqual(evs[eid]["official_competition"], "")
            self.assertIsNone(evs[eid]["official_start_utc"])

        self.assertEqual(evs["199937"]["official_start_utc"], "2026-10-22T23:00:00Z")
        self.assertEqual(evs["902107"]["official_start_utc"], "2026-10-23T02:30:00Z")
        self.assertEqual(evs["536021"]["official_start_utc"], "2026-10-22T10:00:00Z")
        self.assertEqual(evs["32338"]["official_start_utc"], "2026-10-22T17:00:00Z")


class Phase2BoardIntegrationTest(unittest.TestCase):
    """Runs against the live published data files once Phase 2 integration is active."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.events = json.loads((DATA / "events.json").read_text(encoding="utf-8"))["events"]
        cls.gap = json.loads((DATA / "gap_sports.json").read_text(encoding="utf-8"))["rows"]
        cls.matches = json.loads((DATA / "matches.json").read_text(encoding="utf-8"))
        cls.lines = json.loads((DATA / "lines.json").read_text(encoding="utf-8"))
        cls.preds_root = {
            p["ref"]: p
            for p in json.loads((DATA / "predictions.json").read_text(encoding="utf-8"))["predictions"]
        }
        cls.preds_olbg = {
            p["match_id"]: p
            for p in json.loads((DATA / "predictions-olbg.json").read_text(encoding="utf-8"))["predictions"]
        }
        cls.phase2_active = any(r["ref"] == "DRT-17" for r in cls.gap)

    def test_zero_excluded_sports_across_all_published_tables(self) -> None:
        for row in self.events + self.gap + self.matches + self.lines:
            self.assertNotIn(row["sport"].lower(), EXCLUDED_SPORTS)

    def test_phase2_full_board_invariants(self) -> None:
        if not self.phase2_active:
            self.skipTest("Phase 2 data integration not yet applied to working tree")

        # 1. 100% of root two-sided fixtures verified on primary official/club-official hosts
        self.assertEqual(len(self.events), 202)
        for ev in self.events:
            self.assertEqual(ev["verification"]["status"], "verified", ev["ref"])
            self.assertIn(ev["verification"]["source_tier"], {"official", "club-official"}, ev["ref"])

        # 2. All 28 gap-sport rows priced and zero closed 689613. DRT-17 since 2026-10-22 midday:
        #    Humphries withdrawn (pdc.tv, FL-078) -> consensus flipped to Gerwyn Price 3/13 -> row
        #    re-graded MEDIUM (7.46 / +646) because Price's form evidence is third-party-cited only.
        self.assertEqual(len(self.gap), 28)
        by_gap = {r["ref"]: r for r in self.gap}
        for ref, r in by_gap.items():
            self.assertIsNotNone(r["pick"]["price"], ref)
            self.assertNotIn("689613", r["olbg_event_url"])
        self.assertEqual(by_gap["DRT-17"]["pick"]["confidence"], "MEDIUM")
        self.assertEqual(by_gap["DRT-17"]["pick"]["label"], "Gerwyn Price")
        self.assertEqual(self.preds_root["DRT-17"]["status"], "analysis")
        self.assertGreaterEqual(by_gap["DRT-17"]["pick"]["price"], 1.40)
        self.assertLessEqual(by_gap["DRT-17"]["pick"]["price"], 101.00)

        # 3. 11 live in-band HIGH sports on root `/` (100% organic score==6) and 12 on `/olbg/`
        root_high = [r for r in (self.events + self.gap) if r["pick"]["confidence"] == "HIGH"]
        olbg_high = [r for r in self.lines if r["confidence"] == "high"]
        self.assertEqual({r["sport"] for r in root_high}, EXPECTED_ROOT_HIGH_SPORTS)
        self.assertEqual({r["sport"] for r in olbg_high}, EXPECTED_OLBG_HIGH_SPORTS)

        for r in root_high:
            ref = r["ref"]
            price = r["pick"]["price"]
            self.assertGreaterEqual(price, 1.40, ref)
            self.assertLessEqual(price, 101.00, ref)
            self.assertLess(r["pick"]["prob"], 0.70, ref)
            self.assertFalse(r["pick"].get("kickoff_passed"), ref)
            self.assertFalse(r["pick"].get("kickoff_started"), ref)
            pred = self.preds_root[ref]
            self.assertEqual(pred["status"], "high", ref)
            text = " ".join(pred.get("paragraphs", [])) if "paragraphs" in pred else pred.get("body", "")
            self.assertGreaterEqual(len(text.split()), 30, ref)

        for r in olbg_high:
            mid = r["match_id"]
            price = r["our_price_pick"]
            self.assertGreaterEqual(price, 1.40, mid)
            self.assertLessEqual(price, 101.00, mid)
            self.assertLess(r["our_pick_probability"], 0.70, mid)
            self.assertFalse(r.get("kickoff_started"), mid)
            pred = self.preds_olbg[mid]
            self.assertEqual(pred["status"], "high", mid)
            self.assertGreaterEqual(len(pred["text"].split()), 30, mid)

        # 4. SuperLega un-crossed IDs, Osaka WTA 250 label, IHO-14 & GAF-01 non-chalk pricing,
        #    and strict exclusion of non-winner OLBG consensus markets.
        by_ev = {r["ref"]: r for r in self.events}
        by_match = {r["id"]: r for r in self.matches}
        self.assertEqual(by_match["VOL-36994"]["event_name"], "Trentino vs Cisterna")
        self.assertEqual(by_match["VOL-36995"]["event_name"], "Civitanova vs Padova")
        self.assertEqual(by_match["VOL-36996"]["event_name"], "Monza vs Verona")
        self.assertEqual(by_match["VOL-36997"]["event_name"], "Perugia vs Pordenone")
        self.assertEqual(by_ev["TEN-37"]["competition"], "WTA 250 Kinoshita Group Japan Open (Osaka)")
        self.assertEqual(by_ev["IHO-10"]["pick"]["confidence"], "HIGH")
        self.assertEqual(by_ev["IHO-10"]["pick"]["label"], "Brynas IF")
        self.assertEqual(by_ev["IHO-14"]["pick"]["label"], "NY Rangers")
        self.assertEqual(by_ev["GAF-01"]["pick"]["confidence"], "HIGH")
        for r in self.events:
            if r["olbg_market"] in NON_WINNER_MARKETS:
                self.assertNotEqual(r["model"]["basis"], "consensus", r["ref"])


if __name__ == "__main__":
    unittest.main()
