#!/usr/bin/env python3
"""Pins for session-4636f368's repairs (FL-163 to FL-170).

Four published write-ups carried values that the official source read for that match
contradicts or does not state, one build step could silently replace the published
discovery payload with an empty scaffold, and three Volleyball clocks were re-certified
from a fresh read of the same official page.

  FL-163  BKB-29 quoted a 98.2 points-per-game average; the EuroLeague table gives 94.0.
  FL-164  BKB-30 asserted a transfer and a losing streak the cited table does not carry.
  FL-165  IHO-199985 called 41 goals a league high when four clubs had scored more.
  FL-166  BSB-01 published rate stats, a pitch speed and a rest-days claim with no source
          read for the match; only the confirmed facts are kept.
  FL-167  GAF-01 printed a quarter-final score and a five-match aggregate the Cork GAA page
          does not carry.
  FL-168  build_site.py fell back to an empty discovery document on a clean checkout.
  FL-169  five-per-sport target unmet; the reasons are structural, not claims.
  FL-170  the three Volleyball clocks were re-read and re-certified.

The tests are deliberately narrow: they assert the specific claims cannot come back, not
that this session's wording is the only acceptable wording. scripts/build_site.py executes
at import time, so load_discovery() is pulled out with ast rather than imported.
"""
import ast
import datetime as dt
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"


def load(name):
    return json.loads((DATA / name).read_text())


def body(ref):
    return {p["ref"]: p for p in load("predictions.json")["predictions"]}[ref]["body"]


def extract_function(path, name):
    """Compile one module-level function out of a script without executing the script."""
    tree = ast.parse(Path(path).read_text())
    node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == name)
    module = ast.Module(body=[ast.Import(names=[ast.alias(name="json")]),
                              ast.Import(names=[ast.alias(name="os")]),
                              node], type_ignores=[])
    namespace = {}
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[name]


class TestContradictedFiguresAreGone(unittest.TestCase):
    def test_basketball_scoring_average_matches_the_official_table(self):
        text = body("BKB-29")
        self.assertNotIn("98.2", text, "the contradicted average has returned")
        self.assertIn("94.0", text, "the officially derived average is missing")
        # 564 points in six games is 94.0; keep the source numbers next to the average.
        self.assertIn("564", text)
        self.assertIn("524", text)

    def test_basketball_streak_claim_is_gone_and_the_roster_claim_is_sourced(self):
        text = body("BKB-30")
        self.assertNotIn("three-game losing streak", text)
        # The player claim survives only because Valencia's own roster page confirms it.
        self.assertIn("TJ Shorts", text)
        piece = {p["ref"]: p for p in load("predictions.json")["predictions"]}["BKB-30"]
        urls = [s["url"] for s in piece["sources"]]
        self.assertTrue(any("roster" in u for u in urls), "the roster source is not cited")
        self.assertIn("583", text)
        self.assertIn("504", text)

    def test_ice_hockey_no_longer_claims_a_league_high(self):
        text = body("IHO-199985")
        self.assertNotIn("league-high 41", text)
        self.assertIn("47", text, "the clubs with more goals are no longer named")
        self.assertIn("41 goals", text)

    def test_baseball_keeps_what_the_cited_preview_prints_and_drops_the_rest(self):
        # The preview page MLB publishes for this fixture carries the rate stats, the pitch
        # speed, the bullpen line and the rest-days note verbatim, so those stay - but only
        # while the page is cited. The 55-26 home record does not appear on it at all: the
        # standings API assigns that split to Tampa Bay.
        text = body("BSB-01")
        for phrase in ("1.80", "252", "0.80", "104.8", "eleven days", "24-9"):
            self.assertIn(phrase, text, f"figure the cited preview prints is missing: {phrase}")
        self.assertNotIn("55-26", text, "a home record belonging to the other club returned")
        piece = next(p for p in load("predictions.json")["predictions"] if p["ref"] == "BSB-01")
        self.assertTrue(any("starting-lineups-and-pitching-matchup" in s["url"] for s in piece["sources"]),
                        "the preview those figures come from is no longer cited")
        for phrase in ("103-59", "6-4", "Nick Martinez"):
            self.assertIn(phrase, text)

    def test_gaelic_football_drops_the_score_the_county_page_does_not_print(self):
        text = body("GAF-01")
        self.assertNotIn("4-23", text)
        self.assertNotIn("116 points", text)
        self.assertIn("2-12 to 0-16", text)
        self.assertIn("1-20 to 1-17", text)


class TestProseStillSatisfiesTheBrief(unittest.TestCase):
    BANNED = ("model", "verified", "verification")

    def test_every_rebuilt_piece_is_at_least_thirty_words_and_has_no_internal_vocabulary(self):
        for ref in ("BSB-01", "BKB-29", "BKB-30", "IHO-199985", "GAF-01"):
            text = body(ref)
            self.assertGreaterEqual(len(text.split()), 30, ref)
            for word in self.BANNED:
                self.assertNotIn(word, text.lower(), f"{ref} exposes internal vocabulary: {word}")

    def test_every_rebuilt_piece_states_its_selection(self):
        for ref in ("BSB-01", "BKB-29", "BKB-30", "IHO-199985", "GAF-01"):
            lowered = body(ref).lower()
            self.assertTrue(
                any(k in lowered for k in ("selection", "back ", "to win", "is our pick")),
                f"{ref} does not make the betting selection explicit")


class TestVolleyballClocksWereReRead(unittest.TestCase):
    def test_the_three_sunday_fixtures_carry_the_new_read(self):
        events = load("release_checks.json")["events"]
        records_stamp = events["36997"]["checked_at"]
        self.assertGreaterEqual(records_stamp, "2026-10-23T19:30:00Z")
        self.assertEqual(events["36995"]["checked_at"], records_stamp)
        self.assertEqual(events["36996"]["checked_at"], records_stamp)
        for event_id in ("36997", "36995", "36996"):
            record = events[event_id]
            self.assertEqual(record["checked_at"], records_stamp, event_id)
            self.assertEqual(record["timezone"], "UTC")
            self.assertIn("17:00 (UTC)", record["quote"], event_id)
            self.assertTrue(record["source"].startswith("https://en.volleyballworld.com/"))

    def test_the_publication_clock_moved_with_the_read(self):
        events = load("release_checks.json")["events"]
        newest = max(r["checked_at"] for r in events.values() if r.get("checked_at"))
        self.assertGreaterEqual(newest, "2026-10-23T19:30:00Z")


class TestDiscoveryPayloadCannotBeBlanked(unittest.TestCase):
    def setUp(self):
        self.loader = extract_function(ROOT / "scripts" / "build_site.py", "load_discovery")

    def test_the_committed_payload_wins_over_the_empty_scaffold(self):
        payload = self.loader(str(ROOT))
        self.assertTrue(payload.get("sources"), "clean checkout resolved to an empty payload")
        self.assertTrue(payload.get("attempted_at"))

    def test_a_fresh_runtime_capture_still_takes_precedence(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "data").mkdir()
            (Path(tmp) / "data" / "discovery.json").write_text(json.dumps({"attempted_at": "fresh"}))
            (Path(tmp) / "discovery.json").write_text(json.dumps({"attempted_at": "committed"}))
            self.assertEqual(self.loader(tmp)["attempted_at"], "fresh")

    def test_an_absent_payload_is_explicitly_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            payload = self.loader(tmp)
            self.assertEqual(payload["events"], [])
            self.assertEqual(payload["robots"]["state"], "not attempted")


class TestRegisterEntriesExist(unittest.TestCase):
    def test_items_161_to_168_are_published(self):
        ids = {i["id"] for i in load("flagged.json")["items"]}
        for number in range(163, 171):
            self.assertIn(f"FL-{number:03d}", ids)

    def test_every_new_item_carries_a_source_link(self):
        items = {i["id"]: i for i in load("flagged.json")["items"]}
        for number in range(163, 171):
            item = items[f"FL-{number:03d}"]
            self.assertTrue(item.get("sources"), item["id"])
            for source in item["sources"]:
                self.assertTrue(source["url"].startswith("https://"), item["id"])


if __name__ == "__main__":
    unittest.main(verbosity=2)


class TestRegisterReferencesResolve(unittest.TestCase):
    """A citation that points at an id nobody raised is worse than no citation.

    README cross-references the register ~90 times, and renumbering at rebase is exactly
    how a reference comes loose (this pass renumbered its own eight items from FL-161 to
    FL-163 after two siblings had published FL-161/162). Ranges like FL-131..FL-146 are
    written with an ellipsis and are not matched by this pattern.
    """

    def test_every_readme_flag_reference_exists(self):
        import re
        register = {item["id"] for item in load("flagged.json")["items"]}
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        referenced = set(re.findall(r"FL-\d{3}", readme))
        self.assertTrue(referenced)
        self.assertEqual(sorted(referenced - register), [])

    def test_this_pass_kept_the_numbers_it_was_given(self):
        register = {item["id"]: item for item in load("flagged.json")["items"]}
        for number in range(163, 171):
            key = f"FL-{number:03d}"
            self.assertIn(key, register, "this pass's own item was renumbered away")
            self.assertEqual(register[key].get("original_id"), f"FL-{number - 2:03d}", key)
