#!/usr/bin/env python3
"""apply_f00f1bf2.py — publish session-f00f1bf2's written pieces and evidence links.

Everything written here is copied from a committed official capture or a page read in the
session, and every source carries the exact URL it came from:

  * NHL schedule + standings payloads committed by the repository's own probe at
    data/raw/official-20261024T1908Z/json/ (read 2026-10-24T19:08:16Z).
  * EHF Champions League playing-times PDF and standings page, already recorded against
    events 12127..12138 by the 2026-10-23 pass.
  * ECB match page for PAK v ENG (read 2026-10-24T23:0xZ): start printed as
    "13:00 (Local), 04:00 (Your Time)", so the clock is NOT timezone-qualified and the
    piece is published as analysis, never as a HIGH pick.
  * Cricket South Africa fixture page for Eastern Storm v CSA High Performance.
  * WTA official Tokyo singles draw PDF (released 25 Oct 2026 12:36 AM).

Usage: python3 scripts/apply_f00f1bf2.py
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SESSION = "session-f00f1bf2"

NHL_SCHED = "https://api-web.nhle.com/v1/schedule/2026-10-24"
NHL_STAND = "https://api-web.nhle.com/v1/standings/2026-10-24"
EHF_PDF = ("https://ehfel.eurohandball.com/media/jqal4wt0/"
           "ehfcl-men-2026-27-group-phase-playing-times.pdf")
EHF_STAND = "https://ehfcl.eurohandball.com/men/2026-27/standings/"
ECB_MATCH = "https://www.ecb.co.uk/matches/113501/overview"
PCB_BROOK = ("https://www.pcb.com.pk/news-detail/"
             "sri-lanka-seal-second-highest-chase-in-odi-history-as-brook-s-record-"
             "double-ton-goes-in-vain.html")
CSA_MATCH = ("https://cricket.co.za/upcoming-match/"
             "world-sports-betting-eastern-storm-vs-csa-high-performance/")
WTA_DRAW = "https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf"

NEW_SOURCES = [
    {"id": "f00f-nhl-sched-20261024T1908Z", "class": "official",
     "name": "NHL official schedule payload 2026-10-24 (committed probe 19:08Z)",
     "url": NHL_SCHED},
    {"id": "f00f-nhl-stand-20261024T1908Z", "class": "official",
     "name": "NHL official standings payload 2026-10-24 (committed probe 19:08Z)",
     "url": NHL_STAND},
    {"id": "f00f-ecb-pak-eng-20261024", "class": "official",
     "name": "ECB match centre — PAK v ENG, Pakistan ODI Tri-Series (read 2026-10-24)",
     "url": ECB_MATCH},
    {"id": "f00f-pcb-brook-20261022", "class": "official",
     "name": "PCB news — Sri Lanka chase 430 as Brook's double century goes in vain",
     "url": PCB_BROOK},
    {"id": "f00f-csa-eastern-storm-20261024", "class": "official",
     "name": "Cricket South Africa — Eastern Storm v CSA High Performance, Pro20 Cup",
     "url": CSA_MATCH},
    {"id": "f00f-wta-tokyo-draw-20261025", "class": "official",
     "name": "WTA official Toray Pan Pacific Open singles main draw (released 25 Oct 2026)",
     "url": WTA_DRAW},
]

HIGH = [
    {
        "match_id": "ICH-200001",
        "sport": "Ice Hockey",
        "match": "VGS Golden Knights @ CLB Blue Jackets",
        "selection": "Vegas Golden Knights to win (money line)",
        "sources": [
            {"label": "NHL official schedule, 24 Oct 2026 — VGK @ CBJ, 23:00Z, Nationwide Arena",
             "url": NHL_SCHED},
            {"label": "NHL official standings, 24 Oct 2026 — Vegas 8-4-0, Columbus 3-5-0",
             "url": NHL_STAND},
        ],
        "text": (
            "Back the Vegas Golden Knights to win on the money line at Nationwide Arena. Vegas "
            "are 8-4-0 with 46 goals scored and 36 conceded, and they have taken three of five "
            "road games. Columbus are 3-5-0, have managed 20 goals in eight matches and are 3-3-0 "
            "at home, with both clubs arriving on two-game losing runs. The Golden Knights' "
            "scoring depth against a Blue Jackets side that has conceded 29 goals is the basis "
            "for the call, and the visitors' 16:00 local start is the league's own scheduled time."
        ),
    },
    {
        "match_id": "ICH-200004",
        "sport": "Ice Hockey",
        "match": "DET Red Wings @ CGY Flames",
        "selection": "Detroit Red Wings to win (money line)",
        "sources": [
            {"label": "NHL official schedule, 24 Oct 2026 — DET @ CGY, 02:00Z, Scotiabank Saddledome",
             "url": NHL_SCHED},
            {"label": "NHL official standings, 24 Oct 2026 — Detroit 4-3-3, Calgary 3-6-0",
             "url": NHL_STAND},
        ],
        "text": (
            "Take Detroit to win at the Scotiabank Saddledome. Calgary are 3-6-0 and have been "
            "outscored 38-19 across nine games, the heaviest goal difference on Saturday's slate, "
            "even though they have won their past two. The Red Wings are 4-3-3 and 1-0-2 on the "
            "road, and their 30 goals conceded in ten games is the steadier defensive record. "
            "Detroit also won their most recent fixture, so the road side is the selection."
        ),
    },
    {
        "match_id": "ICH-200009",
        "sport": "Ice Hockey",
        "match": "UTA Mammoth @ TB Lightning",
        "selection": "Utah Mammoth to win (money line)",
        "sources": [
            {"label": "NHL official schedule, 24 Oct 2026 — TBL @ UTA, 01:00Z, Delta Center",
             "url": NHL_SCHED},
            {"label": "NHL official standings, 24 Oct 2026 — Utah 7-4-0, Tampa Bay 7-3-0",
             "url": NHL_STAND},
        ],
        "text": (
            "Back Utah to win at the Delta Center. The Mammoth are 7-4-0 with 41 goals scored and "
            "hold a 3-1-0 home record, while Tampa Bay are 7-3-0 overall but 2-3-0 on the road. "
            "Both sides lost their previous match. Utah's home form and higher goal output are the "
            "documented edge, with the Lightning's 29 goals conceded in ten games the reason this "
            "is not a wider call; the hosts are the selection."
        ),
    },
    {
        "match_id": "HAN-12136",
        "sport": "Handball",
        "match": "SC Magdeburg v HC Kriens Luzern",
        "selection": "SC Magdeburg to win (money line)",
        "sources": [
            {"label": "EHF Champions League men 2026/27 group-phase playing times (official PDF)",
             "url": EHF_PDF},
            {"label": "EHF Champions League men 2026/27 official standings and Round 6 calendar",
             "url": EHF_STAND},
        ],
        "text": (
            "Back SC Magdeburg to win their EHF Champions League Round 6 match against HC "
            "Kriens-Luzern at the GETEC Arena on Wednesday. Magdeburg lead Group F with five wins "
            "from five, 176 goals scored and 140 conceded, while the Swiss club are 2-0-3 with 158 "
            "scored and 161 conceded. That unbeaten group record and a 36-goal scoring gap make the "
            "hosts the clear selection for the 20:45 CET throw-off."
        ),
    },
]

ANALYSIS = [
    {
        "match_id": "CRI-188838",
        "sport": "Cricket",
        "match": "Pakistan v England",
        "selection": "Pakistan to win (analysis only: no timezone-qualified clock)",
        "sources": [
            {"label": "ECB match centre — PAK v ENG, Gaddafi Stadium Lahore, 25 Oct 2026", "url": ECB_MATCH},
            {"label": "PCB — Sri Lanka chase 430; Brook's record ODI double century in vain", "url": PCB_BROOK},
        ],
        "text": (
            "Pakistan meet England in the KFC Presents Bank Alfalah ODI Tri-Series at Gaddafi "
            "Stadium, Lahore, on Sunday, and the host board lists the start as 13:00 local and "
            "04:00 reader time. England arrive after a defeat by Sri Lanka in which, the PCB "
            "reports, Harry Brook's record double century went in vain and Sri Lanka completed "
            "the second-highest chase in one-day international history. Pakistan's squad for the "
            "series lists Babar Azam, Shaheen Shah Afridi, Naseem Shah, Haris Rauf, Shadab Khan "
            "and Fakhar Zaman. Back Pakistan to win on home soil, with this labelled a preview "
            "rather than a released pick because the governing body prints only local and reader "
            "time, and neither board publishes a recent-results line here."
        ),
    },
    {
        "match_id": "CRI-188848",
        "sport": "Cricket",
        "match": "Eastern Storm v South Africa Emerging",
        "selection": "Eastern Storm to win (analysis only: fixture-level evidence)",
        "sources": [
            {"label": "Cricket South Africa — Eastern Storm v CSA High Performance, Pro20 Cup",
             "url": CSA_MATCH},
        ],
        "text": (
            "Eastern Storm meet CSA High Performance in the Pro20 Cup 2026/2027 at World Sports "
            "Betting Willowmoore Park Stadium on Sunday, with Cricket South Africa listing a 13:00 "
            "start. Eastern Storm are named first on the governing body's fixture page, and the "
            "venue is the Free State home ground the provincial side uses. Back Eastern Storm to "
            "win, while noting plainly that the page carries no results or form line for either "
            "side, so this rests on the home listing and the competition context rather than on "
            "recent scores, and no total is offered."
        ),
    },
    {
        "match_id": "TEN-902172",
        "sport": "Tennis",
        "match": "Leylah Fernandez v Himeno Sakatsume",
        "selection": "Leylah Fernandez to win (analysis only: no timezone-qualified clock)",
        "sources": [
            {"label": "WTA official Tokyo singles main draw, released 25 Oct 2026", "url": WTA_DRAW},
        ],
        "text": (
            "Leylah Fernandez faces wildcard Himeno Sakatsume in the opening round of the Toray Pan "
            "Pacific Open, according to the official singles draw released on 25 October. The draw "
            "gives Fernandez no seed number and places her in the quarter headed by top seed Elena "
            "Rybakina, while Sakatsume enters on one of the four wildcard places the tournament "
            "lists. Back Fernandez to advance: she is drawn against a wildcard recipient rather "
            "than a seeded player. The WTA publishes no form line or head-to-head with the draw, "
            "so no claim is made about either player's recent results."
        ),
    },
    {
        "match_id": "TEN-902173",
        "sport": "Tennis",
        "match": "Moyuka Uchijima v Elise Mertens",
        "selection": "Elise Mertens to win (analysis only: no timezone-qualified clock)",
        "sources": [
            {"label": "WTA official Tokyo singles main draw, released 25 Oct 2026", "url": WTA_DRAW},
        ],
        "text": (
            "Elise Mertens, seeded fifth in Tokyo, meets Japanese wildcard Moyuka Uchijima in the "
            "first round per the tournament's official draw. The seeded-player list printed with "
            "that draw gives Mertens the fifth of eight seeds, while Uchijima enters on one of the "
            "four wildcard places. Back Mertens to win, with the seeding the published basis for "
            "the call and the home wildcard the counterweight. The draw carries no head-to-head or "
            "recent-results information, so neither is asserted here."
        ),
    },
    {
        "match_id": "TEN-902175",
        "sport": "Tennis",
        "match": "Alexandra Eala v Mika Stojsavljevic",
        "selection": "Alexandra Eala to win (analysis only: no timezone-qualified clock)",
        "sources": [
            {"label": "WTA official Tokyo singles main draw, released 25 Oct 2026", "url": WTA_DRAW},
        ],
        "text": (
            "Alexandra Eala, seeded eighth, plays wildcard Mika Stojsavljevic in the first round of "
            "the Toray Pan Pacific Open, per the official singles draw. Stojsavljevic enters on one "
            "of the four wildcard places the draw lists, and Eala is the seeded player in that "
            "section of the bracket. Back Eala to advance, with the seeding the documented basis "
            "for the selection. No injury or form detail is published with the draw, so none is "
            "claimed."
        ),
    },
]



FLAGS = [
    {
        "id": "FL-218", "severity": "high",
        "title": "Cricket verification record names a different fixture than the row it is keyed to",
        "detail": ("The verification record at data/verifications.json event_verifications[\"188835\"] states "
                   "\"Mpumalanga Rhinos vs CSA High Performance\" while the published OLBG row for that same event id is "
                   "\"South Africa vs Australia\" (31 Oct 2026). The two are not the same match, so the row inherits a "
                   "status of verified for facts belonging to another fixture. No written pick was published on this row; "
                   "the record must be re-read against a Cricket South Africa or Cricket Australia page before it can carry one."),
        "sources": [
            {"label": "Cricket South Africa fixtures (provenance of the mismatched fact)", "url": "https://cricket.co.za/upcoming/"},
            {"label": "OLBG event row for event_id 188835", "url": "https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/South_Africa_vs_Australia/7?event_id=188835"},
        ],
        "status": "needs review",
        "action": "Re-read the fixture from the governing board and either re-key the record or withdraw the verification.",
        "affected_ids": ["CRI-188835"],
    },
    {
        "id": "FL-219", "severity": "medium",
        "title": "OLBG lists Rybakina v Fernandez on 25 Oct, but the official WTA Tokyo draw gives Rybakina a bye and Fernandez Sakatsume",
        "detail": ("The WTA official Toray Pan Pacific Open singles main draw (released 25 Oct 2026 12:36 AM) places Elena Rybakina, "
                   "seed 1, against a bye in the first round, with Leylah Fernandez drawn against wildcard Himeno Sakatsume. OLBG lists "
                   "\"Elena Rybakina vs Leylah Fernandez\" as a fixture on 25 Oct 2026. Both cannot be right. No pick was published on "
                   "the OLBG fixture; the three Tokyo ties that do match the draw were written as analysis only."),
        "sources": [
            {"label": "WTA official Tokyo singles main draw (PDF)", "url": "https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf"},
            {"label": "OLBG event row 902207", "url": "https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Elena_Rybakina_vs_Leylah_Fernandez/3?event_id=902207"},
        ],
        "status": "needs review",
        "action": "Watch the OLBG row until the tournament confirms whether the fixture exists; publish no pick on it meanwhile.",
        "affected_ids": ["TEN-902207"],
    },
    {
        "id": "FL-220", "severity": "medium",
        "title": "Golf: OLBG returned no tip cards on two separate reads while a PGA Tour event was in progress",
        "detail": ("The 17:07Z 2026-10-24 capture recorded zero tip cards on /betting-tips/Golf/5, and a live read at 22:5xZ returned the "
                   "same \"No tips found.\" text. The PGA Tour page captured at 19:08Z shows the Butterfield Bermuda Championship in its "
                   "third round with A. Smotherman leading at -16. No Golf fixture can be published from an empty listing."),
        "sources": [
            {"label": "OLBG Golf listing (live read, \"No tips found.\")", "url": "https://www.olbg.com/betting-tips/Golf/5"},
            {"label": "PGA Tour official schedule/leaderboard page", "url": "https://www.pgatour.com/schedule"},
        ],
        "status": "needs review",
        "action": "Re-read the Golf listing when the next tournament week opens; publish only rows OLBG actually renders.",
        "affected_ids": [],
    },
    {
        "id": "FL-221", "severity": "medium",
        "title": "Snooker: OLBG listing empty on the live read; the single captured card had already finished",
        "detail": ("A live read of /betting-tips/Snooker/8 on 2026-10-24 returned \"No tips found.\" with the expired-events toggle visible. "
                   "The capture taken at 17:07Z carried one snooker card whose start had already passed. With no upcoming snooker fixture "
                   "listed there is nothing to price or write about, and none is published."),
        "sources": [
            {"label": "OLBG Snooker listing (live read)", "url": "https://www.olbg.com/betting-tips/Snooker/8"},
            {"label": "World Snooker Tour matches page (captured, renders client-side)", "url": "https://www.wst.tv/matches/"},
        ],
        "status": "needs review",
        "action": "Retry after the next ranking event is posted; the WST page needs a client-rendered read before clocks can be certified.",
        "affected_ids": [],
    },
    {
        "id": "FL-222", "severity": "low",
        "title": "Greyhounds: 83 captured race cards, none upcoming at the capture clock",
        "detail": ("The 17:07Z capture recorded 83 greyhound cards and every one carried a start earlier than the capture clock, so the sport "
                   "had no upcoming meeting to publish. No greyhound pick is offered; the earlier cards remain in the capture as evidence "
                   "rather than being re-timed."),
        "sources": [
            {"label": "OLBG Greyhounds listing", "url": "https://www.olbg.com/betting-tips/Greyhounds/28"},
            {"label": "GBGB racecard index", "url": "https://www.gbgb.org.uk/racecard"},
        ],
        "status": "needs review",
        "action": "Capture the next afternoon/evening card once OLBG lists it; the GBGB racecard endpoint returned 404 on the last probe.",
        "affected_ids": [],
    },
    {
        "id": "FL-223", "severity": "medium",
        "title": "Both boards price BUF @ WSH differently: the OLBG lines board backs Buffalo, the root board backs Washington",
        "detail": ("For OLBG event 200003 (Buffalo Sabres at Washington Capitals, 2026-10-24 23:00Z) the OLBG lines track originates Buffalo at "
                   "decimal 1.65 (57.6%) while the root board publishes Washington. The tracks use different inputs, so opposite sides are "
                   "possible. The divergence is disclosed here rather than resolved by hand."),
        "sources": [
            {"label": "NHL official schedule 2026-10-24 (fixture 2026020173)", "url": "https://api-web.nhle.com/v1/schedule/2026-10-24"},
            {"label": "NHL official standings 2026-10-24", "url": "https://api-web.nhle.com/v1/standings/2026-10-24"},
        ],
        "status": "needs review",
        "action": "Choose one published side per fixture in a future refresh, and state the basis for the choice.",
        "affected_ids": ["ICH-200003", "IHO-200003"],
    },
    {
        "id": "FL-224", "severity": "medium",
        "title": "Basketball, Darts, Tennis and Cricket fixtures cannot be released: no timezone-qualified clock, or no official page at all",
        "detail": ("The NBA CDN scoreboard endpoint returned HTTP 500 and cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json returned HTTP 403, "
                   "and nba.com/games renders client-side. The captured darts page was empty and the tournament page sits behind a consent wall. "
                   "The WTA draw is readable but prints no start times. The ECB match page prints \"13:00 (Local), 04:00 (Your Time)\" and Cricket "
                   "South Africa prints 13:00 local; neither is timezone-qualified. Those fixtures are published as labelled analysis where a "
                   "written angle exists, never as high-confidence picks."),
        "sources": [
            {"label": "ECB match centre — PAK v ENG (Local / Your Time labels)", "url": "https://www.ecb.co.uk/matches/113501/overview"},
            {"label": "WTA official Tokyo draw (no clocks)", "url": "https://wtafiles.wtatennis.com/pdf/draws/2026/1056/MDS.pdf"},
            {"label": "Cricket South Africa — Eastern Storm v CSA HP, 13:00", "url": "https://cricket.co.za/upcoming-match/world-sports-betting-eastern-storm-vs-csa-high-performance/"},
            {"label": "NBA schedule endpoint (HTTP 403 on the 19:08Z probe)", "url": "https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json"},
        ],
        "status": "needs review",
        "action": "Certify these sports only from a governing-body page that prints an explicit zone; keep the published analysis pieces labelled as analysis.",
        "affected_ids": ["BKB-536111", "BKB-536112", "BKB-536115", "BKB-536118", "DAR-32407",
                          "TEN-902172", "TEN-902173", "TEN-902175", "CRI-188838", "CRI-188848"],
    },
]


def main() -> int:
    ver = json.loads((DATA / "verifications.json").read_text())
    existing_ids = {s["id"] for s in ver["sources"]}
    added_sources = 0
    for source in NEW_SOURCES:
        if source["id"] not in existing_ids:
            ver["sources"].append(source)
            added_sources += 1

    # Attach the two NHL documents to the events whose prose quotes their figures.
    for eid in ("200001", "200004", "200009"):
        record = ver["event_verifications"].setdefault(eid, {})
        record["status"] = "verified"
        record["competition"] = record.get("competition") or "NHL"
        ids = list(record.get("sources") or [])
        for sid in ("f00f-nhl-sched-20261024T1908Z", "f00f-nhl-stand-20261024T1908Z"):
            if sid not in ids:
                ids.append(sid)
        record["sources"] = ids
        facts = list(record.get("facts") or [])
        extra = ("Standings read from the NHL's own 2026-10-24 payload at 19:08Z: "
                 "the figures quoted in this row's written piece are the league's games played, "
                 "wins, losses, overtime losses, goals for and goals against columns.")
        if extra not in facts:
            facts.append(extra)
        record["facts"] = facts

    flag_doc = json.loads((DATA / "flagged.json").read_text())
    known = {item["id"] for item in flag_doc["items"]}
    added_flags = 0
    for flag in FLAGS:
        if flag["id"] not in known:
            flag_doc["items"].append(flag)
            added_flags += 1
    flag_doc["generated_at"] = "2026-10-24T22:58:00Z"
    (DATA / "flagged.json").write_text(
        json.dumps(flag_doc, indent=2, ensure_ascii=False) + "\n")

    (DATA / "verifications.json").write_text(
        json.dumps(ver, indent=2, ensure_ascii=False) + "\n")

    path = DATA / "predictions-olbg.json"
    doc = json.loads(path.read_text())
    mine = {p["match_id"] for p in HIGH} | {p["match_id"] for p in ANALYSIS}
    doc["predictions"] = [p for p in doc["predictions"] if p.get("match_id") not in mine]
    for piece in HIGH:
        doc["predictions"].append(dict(piece, confidence="high", session=SESSION))
    for piece in ANALYSIS:
        doc["predictions"].append(dict(piece, status="analysis", confidence="analysis",
                                       session=SESSION))
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    print(f"flags added: {added_flags}; sources added: {added_sources}; high: {len(HIGH)}; analysis: {len(ANALYSIS)}; "
          f"pieces now: {len(doc['predictions'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
