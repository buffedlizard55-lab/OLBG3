"""Audit tests for session-f00f1bf2 (2026-10-24, task-57).

These lock the two things this session could get wrong without anyone noticing:

* the figures quoted in the newly published ice-hockey and handball prose must still be the
  figures in the committed NHL payload and the committed EHF facts, and
* a fixture that the governing body's own document contradicts must not quietly become a pick.

They are rule tests, not membership pins: they recompute from the committed files.
"""
import datetime as dt
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SESSION = "session-f00f1bf2"


def _load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def _prose(ref):
    for rel in ("data/predictions-olbg.json", "data/predictions.json"):
        for piece in _load(rel)["predictions"]:
            if (piece.get("match_id") or piece.get("ref")) == ref:
                return piece
    raise AssertionError(f"no written piece for {ref}")


def _nhl():
    doc = _load("data/raw/official-20261024T1908Z/json/nhl_standings.json")
    return {row["teamAbbrev"]["default"]: row for row in doc["standings"]}


def _nhl_games():
    doc = _load("data/raw/official-20261024T1908Z/json/nhl_schedule.json")
    games = []
    for week in doc.get("gameWeek", []):
        games.extend(week.get("games", []))
    return games


class NhlProseMatchesPayload(unittest.TestCase):
    CASES = {
        "ICH-200001": ("VGK", "CBJ"),
        "ICH-200004": ("DET", "CGY"),
        "ICH-200009": ("UTA", "TBL"),
    }

    def test_records_and_goals_are_the_committed_ones(self):
        table = _nhl()
        for ref, (pick, opponent) in self.CASES.items():
            text = _prose(ref)["text"]
            allowed_records = set()
            goal_values = set()
            for abbrev in (pick, opponent):
                row = table[abbrev]
                allowed_records.add(f"{row['wins']}-{row['losses']}-{row['otLosses']}")
                # Home and road splits are quoted too; take them from the same payload row.
                for split in ("home", "road"):
                    allowed_records.add(
                        f"{row[split + 'Wins']}-{row[split + 'Losses']}-{row[split + 'OtLosses']}")
                goal_values |= {row["goalFor"], row["goalAgainst"]}
            quoted_records = set(re.findall(r"\b\d{1,2}-\d{1,2}-\d{1,2}\b", text))
            self.assertTrue(quoted_records, f"{ref}: no win-loss record quoted at all")
            self.assertTrue(quoted_records <= allowed_records,
                            f"{ref}: quoted record(s) {quoted_records - allowed_records} "
                            "are not in the committed payload")
            quoted_goals = {int(n) for n in re.findall(r"\b(\d{1,3}) goals\b", text)}
            self.assertTrue(quoted_goals, f"{ref}: no goal count quoted")
            self.assertTrue(quoted_goals <= goal_values,
                            f"{ref}: quoted goal count(s) {quoted_goals - goal_values} "
                            "are not in the committed payload")

    def test_game_is_on_the_committed_schedule_at_the_committed_instant(self):
        starts = {}
        for game in _nhl_games():
            away, home = game["awayTeam"]["abbrev"], game["homeTeam"]["abbrev"]
            away = away.get("default") if isinstance(away, dict) else away
            home = home.get("default") if isinstance(home, dict) else home
            starts[f"{away}@{home}"] = game["startTimeUTC"]
        for ref, (pick, opponent) in self.CASES.items():
            # The row is written from the home side's perspective in the OLBG listing, so accept
            # either orientation but insist the pairing exists and the instant is a Z timestamp.
            pair = [k for k in starts if {pick, opponent} == set(k.split("@"))]
            self.assertTrue(pair, f"{ref}: {pick}/{opponent} not on the committed NHL schedule")
            self.assertRegex(starts[pair[0]], r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


class HighPiecesMeetTheBrief(unittest.TestCase):
    PROHIBITED = ("model", "verified")

    def test_new_high_pieces_are_written_out_and_sourced_twice(self):
        for ref in ("ICH-200001", "ICH-200004", "ICH-200009", "HAN-12136"):
            piece = _prose(ref)
            self.assertEqual(piece.get("confidence"), "high", ref)
            # The published status is clock-derived (a fixture that has kicked off is demoted to
            # analysis by release.sync_predictions), so it is checked against a pinned instant in
            # test_high_pieces_agree_with_the_published_row_pick — never against the live board.
            words = re.findall(r"[A-Za-z0-9']+", piece["text"])
            self.assertGreaterEqual(len(words), 30, ref)
            lowered = piece["text"].lower()
            for banned in self.PROHIBITED:
                self.assertIsNone(re.search(rf"\b{banned}\b", lowered), f"{ref}: {banned}")
            documents = {s["url"] for s in piece["sources"]}
            self.assertGreaterEqual(len(documents), 2, f"{ref}: needs two distinct documents")
            for url in documents:
                self.assertIn(url.split("/")[2].lower(),
                              {"api-web.nhle.com", "ehfel.eurohandball.com",
                               "ehfcl.eurohandball.com"}, ref)

    # Frozen at the certification instant of this batch. The board rebuilds on a moving clock, and
    # a fixture kicking off must demote itself without turning this pin red (the FL-201 lesson).
    PINNED = dt.datetime(2026, 10, 24, 22, 45, tzinfo=dt.timezone.utc)

    def test_high_pieces_agree_with_the_published_row_pick(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import release

        lines = {row["match_id"]: row for row in _load("data/lines.json")}
        for ref in ("ICH-200001", "ICH-200004", "ICH-200009", "HAN-12136"):
            row = lines[ref]
            self.assertIn(row["our_pick"].split()[-1].lower(), _prose(ref)["text"].lower(), ref)
            self.assertTrue(1.40 <= row["our_price_pick"] <= 101.00, ref)
            self.assertLess(row["our_pick_probability"], 0.70, ref)
            assessment = release.assess(ref.split("-")[-1], now=self.PINNED)
            self.assertEqual(assessment["status"], "upcoming", f"{ref}: {assessment.get('reason')}")

    def test_analysis_pieces_stay_analysis(self):
        for ref in ("CRI-188838", "CRI-188848", "TEN-902172", "TEN-902173", "TEN-902175"):
            piece = _prose(ref)
            self.assertEqual(piece.get("status"), "analysis", ref)
            self.assertNotEqual(piece.get("confidence"), "high", ref)


class ContradictedFixturesAreNotPicked(unittest.TestCase):
    def test_rybakina_fernandez_is_flagged_and_unpicked(self):
        flags = {f["id"]: f for f in _load("data/flagged.json")["items"]}
        self.assertIn("FL-219", flags)
        self.assertIn("wtafiles.wtatennis.com", " ".join(s["url"] for s in flags["FL-219"]["sources"]))
        lines = {row["match_id"]: row for row in _load("data/lines.json")}
        if "TEN-902207" in lines:
            self.assertNotEqual(lines["TEN-902207"].get("confidence"), "high")

    def test_mismatched_cricket_record_is_flagged(self):
        flags = {f["id"]: f for f in _load("data/flagged.json")["items"]}
        self.assertIn("FL-218", flags)
        self.assertIn("CRI-188835", flags["FL-218"]["affected_ids"])

    def test_every_clock_blocker_is_flagged(self):
        flags = {f["id"]: f for f in _load("data/flagged.json")["items"]}
        for fid in ("FL-220", "FL-221", "FL-222", "FL-223", "FL-224"):
            self.assertIn(fid, flags)
            self.assertTrue(flags[fid]["sources"], fid)


class EvidenceManifestIsComplete(unittest.TestCase):
    def test_manifest_quotes_every_page_the_prose_relies_on(self):
        manifest = _load("data/raw/fetched-20261024T2240Z-f00f1bf2/manifest.json")
        urls = {p["url"] for p in manifest["pages"]}
        self.assertIn("https://www.ecb.co.uk/matches/113501/overview", urls)
        self.assertIn("https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf", urls)
        for page in manifest["pages"]:
            self.assertTrue(page["quotes"], page["id"])
            self.assertRegex(page["retrieved_at_utc"], r"^\d{4}-\d{2}-\d{2}T")

    def test_withdrawn_figures_are_gone(self):
        """The two claims no read page supported were removed; they must not creep back."""
        text = " ".join(p["text"] for p in _load("data/predictions-olbg.json")["predictions"]
                        if p.get("session") == SESSION)
        self.assertNotIn("114 balls", text)
        self.assertNotIn("ranked twentieth", text)
        self.assertNotIn("rank fifteen", text)


class SiteCaveatIsHonest(unittest.TestCase):
    def test_caveat_no_longer_claims_live_reads_are_impossible(self):
        source = (ROOT / "scripts" / "build_site.py").read_text(encoding="utf-8")
        self.assertNotIn("Live re-verification is blocked in this environment", source)
        self.assertIn("fetched-20261024T2240Z-f00f1bf2", source)
        page = (ROOT / "site" / "brief.html").read_text(encoding="utf-8")
        self.assertNotIn("Live re-verification is blocked in this environment", page)


if __name__ == "__main__":
    unittest.main()
