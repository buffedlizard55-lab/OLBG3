#!/usr/bin/env python3
"""apply_capture.py - append a dated OLBG capture to the board's per-sport capture files.

Input : the capture JSON named by --capture (default: the newest data/raw/olbg-harvest-*.json)
Output: an in-place append to data/sports/<sport>.json

Rules
-----
1. A row is copied verbatim: team/player names, the OLBG date+time label, market, the
   most-tipped selection, the tip counts and the exact OLBG event URL. Nothing is derived
   except the internal `ref`, which is built as ``<PREFIX>-<event_id>`` so it can never
   collide with a hand-numbered ref and always points back at the event it came from.
2. An event that is already on the board (same OLBG event id) is NOT appended twice. The
   existing row already carries the same event URL, and re-adding it would double-count a
   fixture on the coverage table.
3. The capture date is written onto every appended row as ``captured``. The model resolves
   'Today' / 'Tomorrow' against that per-row date, so an old capture can never be silently
   re-read as if it were today's.
4. A sport with no board file (Greyhounds, which is priced on the outright/race track from
   data/raw/gap_sports_capture_20261021.json) is reported, not invented into the board.
5. Nothing is priced, graded or verified here. Those are separate, auditable steps.

Run: python3 scripts/apply_capture.py
"""
from __future__ import annotations

import argparse
import glob
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SPORT_FILE = {
    "Tennis": "tennis.json", "Basketball": "basketball.json", "Golf": "golf.json",
    "Cricket": "cricket.json", "Snooker": "snooker.json", "Rugby Union": "rugby_union.json",
    "Rugby League": "rugby_league.json", "Baseball": "baseball.json",
    "Ice Hockey": "ice_hockey.json", "Motor Racing": "motor_racing.json",
    "Darts": "darts.json", "Handball": "handball.json", "Volleyball": "volleyball.json",
    "Gaelic Football": "gaelic_football.json",
}

PREFIX = {
    "Tennis": "TEN", "Basketball": "BKB", "Golf": "GLF", "Cricket": "CRK", "Snooker": "SNK",
    "Rugby Union": "RGU", "Rugby League": "RGL", "Baseball": "BSB", "Ice Hockey": "IHO",
    "Motor Racing": "MTR", "Darts": "DRT", "Handball": "HBL", "Volleyball": "VOL",
    "Gaelic Football": "GFA", "Greyhounds": "GRY",
}


def newest_capture() -> str:
    files = sorted(glob.glob(os.path.join(ROOT, "data/raw/olbg-harvest-*.json")))
    if not files:
        raise SystemExit("no capture JSON found in data/raw/")
    return files[-1]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--capture", default=None)
    args = ap.parse_args()
    path = args.capture or newest_capture()
    capture = json.load(open(path, encoding="utf-8"))
    captured = capture["capture"][:10]

    board = {}
    seen_ids = set()
    for sport, name in SPORT_FILE.items():
        p = os.path.join(ROOT, "data/sports", name)
        if not os.path.exists(p):
            continue
        doc = json.load(open(p, encoding="utf-8"))
        board[sport] = (p, doc)
        seen_ids.update(e.get("event_id") for e in doc["events"])

    added, skipped, unboarded = [], [], []
    for row in capture["rows"]:
        sport = row["sport"]
        eid = row["event_id"]
        if sport not in board:
            unboarded.append((sport, eid))
            continue
        if eid in seen_ids:
            skipped.append((sport, eid))
            continue
        p, doc = board[sport]
        event = {
            "ref": f"{PREFIX[sport]}-{eid}",
            "competition": row.get("league", ""),
            "home": row["home"],
            "away": row["away"],
            "start": row["start"],
            "market": row["market"],
            "olbg_pick": row["pick"],
            "tips": row["tips"],
            "pct": row["pct"],
            "event_url": f"https://www.olbg.com{row['path']}?event_id={eid}",
            "event_id": eid,
            "captured": captured,
        }
        if row.get("title"):
            event["title"] = row["title"]
        if row.get("listing_order"):
            event["olbg_listing_order"] = row["listing_order"]
        doc["events"].append(event)
        seen_ids.add(eid)
        added.append((sport, event["ref"], row["start"]))

    for sport, (p, doc) in board.items():
        with open(p, "w", encoding="utf-8") as out:
            json.dump(doc, out, indent=2, ensure_ascii=False)
            out.write("\n")

    print(f"capture {os.path.basename(path)} ({captured}): "
          f"{len(added)} appended, {len(skipped)} already on the board, {len(unboarded)} on a non-board track")
    for a in added:
        print("  +", *a)
    for s in skipped:
        print("  = already captured:", *s)
    for u in unboarded:
        print("  ! no board file (race/outright track):", *u)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
