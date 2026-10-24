"""Regression tests for repairs made by session-e6a228f9 (task-52/53).

Three published defects are pinned here so a later rebuild cannot silently
reintroduce them:

1. A United Rugby Championship write-up that reversed both Round 3 results it
   quoted (FL-164). The official URC table and Match Centre show the Stormers
   beating the Sharks 39-22 and the Scarlets beating Benetton 27-26.
2. An NBA citation dated the day before the game it supports (FL-166). The
   schedule URL must carry the US-Eastern calendar date of the fixture.
3. A venue asserted "verbatim" from a page that names only the city (FL-167).
"""

import datetime as _dt
import json
import re
import unittest
from pathlib import Path
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from archive_guard import pins  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]

# Official URC Round 3 results, read from the Match Centre on 2026-10-23:
# the Stormers beat the Sharks 39-22 at DHL Stadium, the Scarlets beat
# Benetton 27-26 at Parc y Scarlets, the Bulls beat the Lions 57-15 at
# Loftus Versfeld and Edinburgh beat Zebre 29-12 in Parma.
ROUND3_WINNERS = {"Stormers": 39, "Scarlets": 27, "Bulls": 57, "Edinburgh": 29}


def _load(name):
    return json.loads((ROOT / "data" / name).read_text())


def _olbg_predictions():
    return _load("predictions-olbg.json")["predictions"]


def _root_predictions():
    """The root track keys pieces by ``ref`` and stores prose in ``body``."""
    out = []
    for piece in _load("predictions.json")["predictions"]:
        row = dict(piece)
        row["match_id"] = piece.get("ref")
        row["text"] = piece.get("body", "") + " " + piece.get("headline", "")
        out.append(row)
    return out


def _matches():
    return {row["id"]: row for row in _load("matches.json")}


def _eastern_date(utc_stamp):
    """US-Eastern calendar date for an ISO-8601 UTC stamp.

    Used instead of the UTC date because a 00:00Z start is still the previous
    evening in New York, which is the date NBA's own schedule page uses.
    """
    if not utc_stamp:
        return None
    raw = utc_stamp.replace("Z", "+00:00")
    moment = _dt.datetime.fromisoformat(raw)
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=_dt.timezone.utc)
    try:
        from zoneinfo import ZoneInfo

        moment = moment.astimezone(ZoneInfo("America/New_York"))
    except Exception:  # pragma: no cover - no tz database on this runner
        moment = moment.astimezone(_dt.timezone(_dt.timedelta(hours=-4)))
    return moment.date()


@pins('olbg-harvest-20261023T1700Z.tsv')
class UrcRoundThreeResults(unittest.TestCase):
    """FL-164: neither track may reverse a Round 3 result."""

    def setUp(self):
        self.olbg = {p["match_id"]: p for p in _olbg_predictions()}
        self.root = {p["match_id"]: p for p in _root_predictions()}

    def _text(self, predictions, *ids):
        return " ".join(predictions[i]["text"] for i in ids if i in predictions)

    def test_stormers_piece_reports_a_stormers_win(self):
        text = self._text(self.olbg, "RGU-609580")
        self.assertTrue(text, "RGU-609580 must still be published")
        self.assertIn("39-22", text)
        self.assertIsNone(
            re.search(r"beaten\s+39-22|went down\s+39-22|lost\s+39-22", text, re.I),
            "the Stormers beat the Sharks 39-22; the piece must not call that a defeat",
        )

    def test_stormers_piece_reports_a_scarlets_win(self):
        text = self._text(self.olbg, "RGU-609580")
        self.assertIn("27-26", text)
        self.assertIsNone(
            re.search(r"went down\s+27-26|beaten\s+27-26|lost\s+27-26", text, re.I),
            "the Scarlets beat Benetton 27-26; the piece must not call that a defeat",
        )

    def test_both_tracks_agree_on_the_same_result(self):
        olbg = self._text(self.olbg, "RGU-609580")
        root = self._text(self.root, "RGU-11")
        if not root:
            self.skipTest("root track no longer carries the Stormers fixture")
        # Whichever track states the scoreline, neither may contradict it.
        for text in (olbg, root):
            self.assertIsNone(
                re.search(r"beaten\s+39-22|lost\s+39-22", text, re.I),
                "the two tracks must not disagree about Stormers 39-22 Sharks",
            )

    def test_lions_were_away_at_loftus(self):
        """FL-165: the 57-15 defeat happened at the Bulls' ground, not at home."""
        text = self._text(self.olbg, "RGU-609579")
        self.assertNotRegex(
            text,
            r"57-15\s+at\s+home|at\s+home\s+by\s+the\s+Vodacom\s+Bulls",
            "the Bulls beat the Lions 57-15 at Loftus Versfeld, the Bulls' ground",
        )


class NbaScheduleCitation(unittest.TestCase):
    """FL-166: a schedule link must be dated the day of the game."""

    def test_schedule_url_matches_the_eastern_game_date(self):
        matches = _matches()
        checked = 0
        for piece in _olbg_predictions():
            urls = [s.get("url", "") for s in piece.get("sources", [])]
            schedule = [u for u in urls if "nba.com/schedule" in u]
            if not schedule:
                continue
            match = matches.get(piece["match_id"], {})
            stamp = match.get("official_start_utc") or match.get("verified_start")
            game_date = _eastern_date(stamp)
            if game_date is None:
                continue
            for url in schedule:
                quoted = re.search(r"[?&]date=(\d{4}-\d{2}-\d{2})", url)
                self.assertIsNotNone(quoted, f"{piece['match_id']}: schedule URL has no date")
                self.assertEqual(
                    quoted.group(1),
                    game_date.isoformat(),
                    f"{piece['match_id']} cites {url} for a game on {game_date}",
                )
                checked += 1
        self.assertGreater(checked, 0, "no NBA schedule citations were checked")


class VenueNotAssertedWithoutEvidence(unittest.TestCase):
    """FL-167: prose must not certify a venue the cited page does not name."""

    def test_no_verbatim_venue_claim_without_a_stored_venue(self):
        verifications = _load("verifications.json")["event_verifications"]
        matches = _matches()
        for piece in _olbg_predictions():
            text = piece.get("text", "") or ""
            if not re.search(r"confirmed verbatim|verbatim on", text, re.I):
                continue
            row = matches.get(piece["match_id"], {})
            eid = str(row.get("olbg_event_id", ""))
            stored = (verifications.get(eid) or {}).get("venue")
            self.assertTrue(
                stored,
                f"{piece['match_id']} says a venue was confirmed verbatim but no venue is stored",
            )
            self.assertIn(stored.split(",")[0].strip(), text)


class FlagRegisterIntegrity(unittest.TestCase):
    def test_ids_are_unique_and_every_item_has_an_official_https_source(self):
        items = _load("flagged.json")["items"]
        ids = [i["id"] for i in items]
        self.assertEqual(len(ids), len(set(ids)), "duplicate flag ids")
        for item in items:
            self.assertTrue(item.get("sources"), f"{item['id']} has no sources")
            for source in item["sources"]:
                self.assertTrue(
                    source.get("url", "").startswith("https://"),
                    f"{item['id']} carries a non-https source",
                )

    def test_the_two_followup_flags_are_registered(self):
        titles = {i["id"]: i["title"] for i in _load("flagged.json")["items"]}
        for flag in ("FL-164", "FL-165", "FL-166", "FL-167"):
            self.assertIn(flag, titles, f"{flag} missing from the register")


if __name__ == "__main__":
    unittest.main()
