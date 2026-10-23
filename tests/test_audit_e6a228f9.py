"""Pins the source-link repair of 2026-10-23 (FL-161).

The defect
----------
`tools/build_dataset.py` built every published OLBG event URL as

    https://www.olbg.com/betting-tips/{path_prefix}/{slug}/{sport_id}?event_id={eid}

which is right for a *v2* capture row, where `path_prefix` stops at the competition
(`Tennis/All_Tennis/All_Events`). The *v3* capture stores `path_prefix` as the href's path up to the
sport id, so it already ends in the slug:

    Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers

Appending the slug a second time produced

    .../TB_Rays_@_MIL_Brewers/TB_Rays_@_MIL_Brewers/12?event_id=160789

which OLBG answers with **404**. That was the `olbg_url` of 177 of the 180 published rows: none of
them equalled the href the server had actually rendered, so every "OLBG event page" source link on
`/olbg/` was dead while still reading as evidence. Re-fetched live on 2026-10-23T19:33Z: the served
href renders the event page, the published one 404s.

What is asserted here
---------------------
1. For every published row whose event id appears in the committed 17:00Z capture, `olbg_url` is
   byte-identical to an href present in that capture's served HTML. This is the actual repair.
2. No published row repeats its final path segment.
3. The helper still appends the slug when the prefix is a v2-style competition path, so the three
   rows that come from the supplementary v2 capture keep their working URLs.
4. The rows carried from the v2 supplementary capture resolve to pages that exist (checked as URL
   shape here; the live fetch is recorded in docs/audit-e6a228f9.md).

These are regression pins on committed evidence. They make no claim about a match and re-verify no
sporting fact.
"""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import build_dataset as bd  # noqa: E402

CAPTURE = ROOT / "data/raw/live-20261023T1700Z/listings"
HREF_RE = re.compile(r'href="(https://www\.olbg\.com/betting-tips/[^"]*event_id=(\d+))"')


def served_hrefs() -> dict[str, set[str]]:
    hrefs: dict[str, set[str]] = {}
    for f in sorted(CAPTURE.glob("*.html")):
        for url, eid in HREF_RE.findall(f.read_text(errors="replace")):
            hrefs.setdefault(eid, set()).add(url)
    return hrefs


def match_rows() -> list[dict]:
    return json.loads((ROOT / "data/matches.json").read_text())


class PublishedLinkMatchesTheServedHref(unittest.TestCase):
    def setUp(self):
        self.hrefs = served_hrefs()
        self.rows = match_rows()

    def test_the_capture_still_holds_the_evidence(self):
        # If this fails the capture was replaced, not repaired, and every assertion below is void.
        self.assertEqual(len(self.hrefs), 177)

    def test_every_row_with_a_captured_href_publishes_that_exact_href(self):
        checked = 0
        for row in self.rows:
            eid = re.search(r"event_id=(\d+)", row["olbg_url"] or "")
            if not eid or eid.group(1) not in self.hrefs:
                continue
            self.assertIn(row["olbg_url"], self.hrefs[eid.group(1)],
                          f"{row['id']} publishes a link the server never rendered")
            checked += 1
        # 177 of 180 rows come from the v3 capture; the other three come from the v2 supplement
        # and have no href in it, which is why they are skipped rather than asserted.
        self.assertEqual(checked, 177)

    def test_no_row_repeats_its_final_path_segment(self):
        for row in self.rows:
            seg = re.search(r"/betting-tips/(.+)/\d+\?event_id=", row["olbg_url"] or "")
            self.assertIsNotNone(seg, row["id"])
            parts = seg.group(1).split("/")
            if len(parts) >= 2:
                self.assertNotEqual(parts[-1], parts[-2], f"{row['id']} repeats a path segment")

    def test_the_three_supplementary_rows_still_name_their_own_event(self):
        # These came from the 16:30Z v2 supplement (no startDate attribute, no href). Their URLs
        # must still be competition/slug/id shaped, and the slug must name the fixture OLBG does.
        supplements = {r["id"]: r for r in self.rows
                       if r["id"] in ("TEN-902147", "GRY-689803", "GRY-689800")}
        self.assertEqual(len(supplements), 3)
        expected = {
            "TEN-902147": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/"
                          "Luca_Van_Assche_vs_Lorenzo_Musetti/3?event_id=902147",
            "GRY-689803": "https://www.olbg.com/betting-tips/Greyhounds/All_Greyhounds/All_Events/"
                          "5:12_Towcester/28?event_id=689803",
            "GRY-689800": "https://www.olbg.com/betting-tips/Greyhounds/All_Greyhounds/All_Events/"
                          "5:18_Kinsley/28?event_id=689800",
        }
        for mid, url in expected.items():
            self.assertEqual(supplements[mid]["olbg_url"], url, mid)


class UrlBuilder(unittest.TestCase):
    def test_v3_prefix_already_holding_the_slug_is_not_appended_again(self):
        self.assertEqual(
            bd.event_url("Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers", "TB_Rays_@_MIL_Brewers", 12, "160789"),
            "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160789")

    def test_v2_competition_prefix_still_gets_the_slug(self):
        self.assertEqual(
            bd.event_url("Tennis/All_Tennis/All_Events", "Ann_Li_vs_Ashlyn_Krueger", 3, "902157"),
            "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/"
            "Ann_Li_vs_Ashlyn_Krueger/3?event_id=902157")

    def test_a_bare_slug_prefix_is_not_repeated(self):
        # No capture has ever produced a bare-slug prefix; the row would lose its competition path,
        # so the point of this case is only that the slug is not emitted twice.
        self.assertEqual(bd.event_url("Ann_Li_vs_Ashlyn_Krueger", "Ann_Li_vs_Ashlyn_Krueger", 3, "902157"),
                         "https://www.olbg.com/betting-tips/Ann_Li_vs_Ashlyn_Krueger/3?event_id=902157")

    def test_slashes_around_the_prefix_do_not_double_up(self):
        self.assertEqual(bd.event_url("/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/", "TB_Rays_@_MIL_Brewers", 12, "1"),
                         "https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=1")




# ---------------------------------------------------------------------------------------------
# Second half of the task: what the repaired links actually say.
#
# Re-read live on 2026-10-23 against the URC Match Centre table, the MLB standings and playoff
# schedule, the Cork GAA results hub and the Volleyball World match pages. The checks below encode
# the four defects that re-read produced (FL-162..FL-165), each as a general rule rather than a
# string pin where a general rule is available.
# ---------------------------------------------------------------------------------------------

import datetime as _dt  # noqa: E402


def olbg_pieces() -> dict[str, dict]:
    return {p["match_id"]: p for p in json.loads((ROOT / "data/predictions-olbg.json").read_text())["predictions"]}


class UrcRoundThreeResultsAgreeAcrossTheTracks(unittest.TestCase):
    """FL-162/FL-163: both tracks must describe the same official Round 3 results.

    The URC table page (stats.unitedrugby.com/match-centre/table/2026-27) carries the Round 3 strip:
    Loftus Versfeld BUL 57 - LIO 15; DHL Stadium STO 39 - SHA 22; Parc y Scarlets SCA 27 - BEN 26.
    The root track had these right; two /olbg pieces did not.
    """

    def setUp(self):
        self.olbg = olbg_pieces()
        root = json.loads((ROOT / "data/predictions.json").read_text())["predictions"]
        self.root = {p.get("ref"): p for p in root}

    def test_the_stormers_won_39_22_and_scarlets_won_27_26_wherever_the_result_is_stated(self):
        piece = self.olbg["RGU-609580"]["text"]
        self.assertIn("beat Hollywoodbets Sharks 39-22", piece)
        self.assertIn("edged Benetton 27-26", piece)
        for wrong in ("beaten 39-22", "went down 27-26", "opened Round 3 badly"):
            self.assertNotIn(wrong, piece, "a reversed Round 3 result is back")

    def test_the_two_tracks_do_not_disagree_about_the_same_match(self):
        root = self.root["RGU-11"]["body"]
        piece = self.olbg["RGU-609580"]["text"]
        self.assertIn("39-22", root)
        self.assertIn("39-22", piece)
        # 'overpowered' in one track and 'beaten by' in the other cannot both be true
        self.assertNotIn("beaten by the Sharks", piece)
        self.assertNotIn("lost 39-22", piece)

    def test_the_lions_were_away_at_loftus_not_at_home(self):
        piece = self.olbg["RGU-609579"]["text"]
        self.assertIn("away by the Vodacom Bulls at Loftus Versfeld", piece)
        self.assertNotIn("at home by the Vodacom Bulls", piece)


class OfficialSourceDatesSupportTheirClaim(unittest.TestCase):
    """FL-164: a schedule citation must be dated the day of the fixture it evidences."""

    @staticmethod
    def _game_day(row: dict) -> _dt.date | None:
        """The day the league itself lists the game on, which is not always the UTC date.

        A 00:00Z or 01:30Z start is still the previous evening in New York, and the NBA schedule
        page is indexed by that local day - BKB-534841 tips at 01:30Z on 24 October but appears on
        the 23 October page. Converting the official clock to Eastern is what makes the comparison
        mean the same thing as the citation.
        """
        start = row.get("official_start_utc") or row.get("olbg_start_utc")
        if start:
            from zoneinfo import ZoneInfo
            moment = _dt.datetime.fromisoformat(start.replace("Z", "+00:00"))
            return moment.astimezone(ZoneInfo("America/New_York")).date()
        return _dt.date.fromisoformat(row["date_iso"]) if row.get("date_iso") else None

    def test_no_piece_cites_a_schedule_day_other_than_its_fixture_day(self):
        matches = {m["id"]: m for m in match_rows()}
        cited = 0
        for mid, piece in olbg_pieces().items():
            row = matches.get(mid)
            if not row:
                continue
            game_day = self._game_day(row)
            if game_day is None:
                continue
            for url in re.findall(r'https://www\.nba\.com/schedule\?date=(\d{4}-\d{2}-\d{2})', json.dumps(piece)):
                self.assertEqual(_dt.date.fromisoformat(url), game_day,
                                 f"{mid} cites the {url} NBA schedule for a game on {game_day}")
                cited += 1
        self.assertGreater(cited, 0, "no NBA schedule citation was checked")


class NoVenueIsAttributedToASourceThatDoesNotStateIt(unittest.TestCase):
    """FL-165: 'confirmed verbatim' may only be claimed for a value the cited page carries."""

    def test_a_blank_verified_venue_is_not_asserted_as_verbatim(self):
        ver = json.loads((ROOT / "data/verifications.json").read_text())["event_verifications"]
        for mid, piece in olbg_pieces().items():
            eid = mid.split("-", 1)[1]
            ev = ver.get(eid) or {}
            if ev.get("venue"):
                continue
            self.assertNotIn("confirmed verbatim on FIVB", piece["text"],
                             f"{mid} claims a verbatim venue while its verification record has none")

    def test_the_volleyball_piece_only_carries_what_the_match_page_states(self):
        piece = olbg_pieces()["VOL-36997"]["text"]
        self.assertIn("in Perugia", piece)
        self.assertIn("17:00 UTC", piece)
        self.assertIn("Reggers", piece)
        self.assertNotIn("PalaBarton", piece)
        self.assertNotIn("newly promoted", piece)


if __name__ == "__main__":
    unittest.main()
