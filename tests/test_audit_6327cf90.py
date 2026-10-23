#!/usr/bin/env python3
"""Audit for session-6327cf90's net-new contributions on top of the 2026-10-23 passes.

Six parallel sessions landed PRs #119-#136 while this one was running and between them already
published the 2026-10-23 harvest, the NHL/MLB/URC clock re-observations, the banned-word sweep and
the Stormers clock repair. This session's daily pass was therefore superseded and was NOT merged;
what follows are the four defects it found that main did not have, each pinned so it cannot return.

  FL-156  parse_tips() failed on OLBG's rendered "N/M Win Tips" label, so 167 of 180 rows were
          priced from a home-court baseline while disclosing a tip split that was never used.
  FL-157  the tennis label "Total Games" sat in one of three market-label sets that must agree.
  FL-158  two CBV verification records held a different fixture's venue and kick-off while
          publishing as confirmed against the national federation.
  FL-159  three write-ups asserted form no cited source supports; one contradicted the official
          ASOBAL table this project already holds, and its row had picked the wrong side.

Note that scripts/model.py executes at import time, so the market-label sets here are read with ast
rather than imported: importing it would rebuild the board as a side effect of running a test.
"""
import ast
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "tools"))

from build_dataset import OTHER_MARKETS, parse_tips  # noqa: E402


def load(name):
    return json.loads((DATA / name).read_text())


def set_literal(path, name):
    """Pull a module-level set literal out of a script without executing it."""
    tree = ast.parse(Path(path).read_text())
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return set(ast.literal_eval(node.value))
    raise AssertionError(f"{name} not found at module level in {path}")


class TestTipCountParsing(unittest.TestCase):
    """FL-156: the count is in the captured string; the parser must read it, not discard it."""

    def test_reads_the_label_olbg_actually_renders(self):
        self.assertEqual((25, 31), parse_tips("25/31 Win Tips"))
        self.assertEqual((2, 2), parse_tips("2/2 Win Tips"))
        self.assertEqual((7, 8), parse_tips("7/8"))
        self.assertEqual((1, 1), parse_tips(" 1 / 1 Win Tips "))

    def test_still_returns_nothing_when_there_is_no_count(self):
        for value in ("", None, "Win Tips", "no tips", "3-1", "Over 22.50"):
            self.assertEqual((None, None), parse_tips(value), repr(value))

    def test_does_not_pick_up_a_stray_fraction_later_in_the_label(self):
        self.assertEqual((22, 50), parse_tips("22/50 and then 3/4"))

    def test_no_board_row_loses_a_count_the_source_rendered(self):
        """The durable invariant: a captured N/M label must never publish a null count."""
        offenders = []
        for m in load("matches.json"):
            tips = m.get("olbg_tips") or ""
            if re.match(r"^\s*\d+\s*/\s*\d+", tips) and m.get("olbg_tips_won") is None:
                offenders.append((m["id"], tips))
        self.assertEqual([], offenders)

    def test_basis_claiming_a_tip_split_actually_had_one(self):
        """FL-156's real harm: 77 rows disclosed a shrink of a tip split that was never read."""
        offenders = []
        for line in load("lines.json"):
            basis = (line.get("inputs") or {}).get("basis") or ""
            if "OLBG tip split shrunk" in basis and (line.get("inputs") or {}).get("p_raw") is None:
                offenders.append(line["match_id"])
        self.assertEqual([], offenders)

    def test_the_vast_majority_of_rows_now_parse(self):
        matches = load("matches.json")
        with_tips = [m for m in matches if m.get("olbg_tips")]
        parsed = [m for m in with_tips if m.get("olbg_tips_won") is not None]
        self.assertGreater(len(parsed) / len(with_tips), 0.98,
                           f"{len(parsed)}/{len(with_tips)} parsed")

    def test_outright_markets_are_priced_rather_than_left_null(self):
        """Motor Racing, Darts and Rugby League outrights had no originated price at all."""
        lines = {l["match_id"]: l for l in load("lines.json")}
        for mid in ("MTR-913", "MTR-828", "MTR-912", "DAR-26023", "RGL-2695857", "RGL-2801600"):
            if mid in lines:
                self.assertIsNotNone(lines[mid].get("our_price_pick"), mid)


class TestMarketLabelSetsStayInStep(unittest.TestCase):
    """FL-157: three sets classify market labels and a label missing from one is classified by fallback."""

    def test_all_three_sets_agree(self):
        dataset = OTHER_MARKETS - {""}   # the blank label is a Gaelic row rendering no market at all
        board = set_literal(ROOT / "scripts/model.py", "NON_WIN_CONSENSUS_MARKETS")
        source = (ROOT / "tools/originate.py").read_text()
        block = re.search(r"_non_win = \{(.*?)\}", source, re.S).group(1)
        olbg = set(ast.literal_eval("{" + block + "}"))
        self.assertEqual(dataset, board, "build_dataset OTHER_MARKETS vs model NON_WIN_CONSENSUS_MARKETS")
        self.assertEqual(dataset, olbg, "build_dataset OTHER_MARKETS vs originate _non_win")

    def test_total_games_is_present_in_all_three(self):
        self.assertIn("Total Games", OTHER_MARKETS)
        self.assertIn("Total Games",
                      set_literal(ROOT / "scripts/model.py", "NON_WIN_CONSENSUS_MARKETS"))
        self.assertIn('"Total Games"', (ROOT / "tools/originate.py").read_text())


class TestWithdrawnCBVRecords(unittest.TestCase):
    """FL-158: blank and flag, never infer the right value from a neighbouring row."""

    MISMATCHED = {"37002": "Mackenzie", "37003": "Brusque"}

    def test_venue_and_clock_are_blank_and_status_is_not_verified(self):
        ver = load("verifications.json")["event_verifications"]
        for eid in self.MISMATCHED:
            rec = ver[eid]
            self.assertIsNone(rec.get("venue"), eid)
            self.assertIsNone(rec.get("start_local"), eid)
            self.assertEqual("unverified", rec.get("status"), eid)

    def test_the_withdrawn_values_are_kept_for_the_audit_trail(self):
        ver = load("verifications.json")["event_verifications"]
        self.assertEqual("Arena Paulo Skaf, Bauru", ver["37002"]["previous_venue"])
        self.assertEqual("2026-10-24 21:00 BRT", ver["37002"]["previous_start_local"])
        self.assertEqual("Sportville, Barueri", ver["37003"]["previous_venue"])
        for eid in self.MISMATCHED:
            self.assertIn("MISMATCH", " ".join(ver[eid]["facts"]))

    def test_the_blank_propagated_onto_the_published_row(self):
        matches = {m["id"]: m for m in load("matches.json")}
        for mid in ("VOL-37002", "VOL-37003"):
            self.assertIsNone(matches[mid]["venue"], mid)
            self.assertIsNone(matches[mid]["verified_start"], mid)
            self.assertEqual("unverified", matches[mid]["verification_status"], mid)

    def test_the_two_matching_cbv_rows_were_left_alone(self):
        ver = load("verifications.json")["event_verifications"]
        for eid in ("37000", "37001"):
            self.assertIsNotNone(ver[eid].get("venue"), eid)
            self.assertEqual("verified", ver[eid].get("status"), eid)


class TestProseMatchesItsSources(unittest.TestCase):
    """FL-159: no claim the cited source cannot carry, and no figure the held table contradicts."""

    def pieces(self):
        return {p["match_id"]: p for p in load("predictions-olbg.json")["predictions"]}

    def test_the_contradicted_handball_statistics_are_gone(self):
        text = self.pieces()["HAN-12107"]["text"]
        for claim in ("four wins from five", "plus 18", "+18", "three of their four away"):
            self.assertNotIn(claim, text, f"piece still asserts {claim!r}")

    def test_the_piece_now_carries_the_official_asobal_numbers(self):
        text = self.pieces()["HAN-12107"]["text"]
        for fact in ("177", "211", "-34", "182", "184"):
            self.assertIn(fact, text, f"official ASOBAL figure {fact} missing from the piece")
        self.assertTrue(any("asobal.es" in s["url"] for s in self.pieces()["HAN-12107"]["sources"]))

    def test_the_withdrawn_venues_no_longer_appear_in_prose(self):
        for mid, venue in (("VOL-37002", "Bauru"), ("VOL-37003", "Barueri")):
            piece = self.pieces()[mid]
            self.assertNotIn(venue, piece["selection"])
            # the body may mention the arena only to say the claim was withdrawn
            if venue in piece["text"]:
                self.assertRegex(piece["text"], r"not (?:Mackenzie|Brusque)'s home")

    def test_no_piece_cites_only_a_bare_homepage(self):
        from urllib.parse import urlparse
        offenders = []
        for mid, piece in self.pieces().items():
            urls = [s.get("url", "") for s in piece.get("sources") or [] if isinstance(s, dict)]
            if urls and all(urlparse(u).path.strip("/") in ("", "en", "www") for u in urls):
                offenders.append(mid)
        self.assertEqual([], offenders)

    def test_the_handball_pick_agrees_with_the_official_table(self):
        """The table this project holds gives Puerto Sagunto 4 points and Villa de Aranda 1."""
        asobal = load("official.json")["form_data"]["Handball_Spain_ASOBAL_2026_27"]["teams"]
        self.assertGreater(asobal["Fertiberia Puerto Sagunto"]["pts"],
                           asobal["Tubos Aranda Villa de Aranda"]["pts"])
        lines = {l["match_id"]: l for l in load("lines.json")}
        self.assertEqual("Puerto Sagunto", lines["HAN-12107"]["our_pick"])


if __name__ == "__main__":
    unittest.main()
