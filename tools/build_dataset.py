#!/usr/bin/env python3
"""Parse the raw OLBG harvest into a structured dataset.

Inputs : the harvest named by data/meta.json["harvest_file"] (v1: olbg-harvest-20261021.tsv,
         v2: olbg-harvest-20261021T0650Z.tsv), data/meta.json, data/verifications.json
Outputs: data/matches.json

Rules enforced here:
  * every row keeps the exact OLBG URL it came from
  * a field is only populated when the harvest or a cited verification states it
  * nothing is guessed: unknown stays null
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SPORT_IDS = {
    "Cricket": 7, "Tennis": 3, "Basketball": 4, "Snooker": 8, "Darts": 15,
    "Rugby Union": 9, "Rugby League": 10, "Ice Hockey": 13, "Baseball": 12,
    "Volleyball": 21, "Handball": 20, "Golf": 5, "Motor Racing": 14,
    "Gaelic Football": 25, "Greyhounds": 28,
}

ID_PREFIX = {
    "Cricket": "CRI", "Tennis": "TEN", "Basketball": "BKB", "Snooker": "SNO",
    "Darts": "DAR", "Rugby Union": "RGU", "Rugby League": "RGL", "Ice Hockey": "ICH",
    "Baseball": "BSB", "Volleyball": "VOL", "Handball": "HAN", "Golf": "GLF",
    "Motor Racing": "MTR", "Gaelic Football": "GFA", "Greyhounds": "GRY",
}

# OLBG appends a format descriptor to some cricket fixture names ("... 1st T20 Match").
# Stripping it is pure string normalisation; the untouched name is kept in event_name.
SUFFIX_RE = re.compile(r"\s+(One Day Match|1st T20 Match|2nd T20 Match|3rd T20 Match|T20|1st ODI|2nd ODI|3rd ODI)$")

# "Win Race" is a multi-runner outright field market, not a two-sided match. The only OLBG row
# using it is MTR-913, the 22-driver Formula 1 USA Grand Prix (no home/away sides). It must be
# priced through the field-prior branch in originate.py; keeping it in WIN_MARKETS routed it to
# the two-way fallback (p_base=0.52 -> -120), contradicting its own +235/3.35 prediction.
# Moved 2026-10-22 (session-f0f3be65); see FL-047.
WIN_MARKETS = {"Win Match", "Win Match 2-way", "Money Line", "To Win"}
OUTRIGHT_MARKETS = {"Win Tournament", "Grand Final Winner", "Daily Races", "Outright Winner",
                    "Fastest Qualifier", "Win Race"}
OTHER_MARKETS = {"Total Legs", "Total Games", "Game Totals", "Puck Line", "Handicap", "Handicap 2-way",
                 "Match Handicap", "Pointspread", "Set Betting", "Set Score", "1st Set Winner", "Games Won", "Man Of The Match", ""}


def competition_status(ev: dict) -> str:
    """'verified' only when an official/primary-class record names the competition."""
    if not ev.get("competition"):
        return "not_stated_by_source"
    st = ev.get("status") or "unverified"
    if st in ("verified", "verified_market_row"):
        return "verified"
    if st == "verified_secondary_only":
        return "corroborated_only"
    return "partial"


def parse_tips(tips: str) -> tuple[int | None, int | None]:
    if not tips or "/" not in tips:
        return None, None
    won, total = tips.split("/", 1)
    try:
        return int(won), int(total)
    except ValueError:
        return None, None


def split_teams(event: str) -> tuple[str | None, str | None]:
    """Mechanical split only - OLBG's own separator, no inference."""
    if " @ " in event:
        away, home = event.split(" @ ", 1)
        return home.strip(), away.strip()
    if " vs " in event:
        home, away = event.split(" vs ", 1)
        return home.strip(), away.strip()
    if " v " in event:
        home, away = event.split(" v ", 1)
        return home.strip(), away.strip()
    return None, None


def resolve_date(label: str, run_day: date) -> str | None:
    """Only resolves the two relative labels OLBG itself uses."""
    label = label.strip()
    if label == "Today":
        return run_day.isoformat()
    if label == "Tomorrow":
        return (run_day + timedelta(days=1)).isoformat()
    m = re.match(r"^(\d{1,2}) (\w{3})$", label)
    if m:
        day = int(m.group(1))
        month = datetime.strptime(m.group(2), "%b").month
        year = run_day.year if month >= run_day.month else run_day.year + 1
        return date(year, month, day).isoformat()
    m = re.match(r"^(\d{1,2}) (\w{3}) (\d{4})$", label)
    if m:
        return datetime.strptime(label, "%d %b %Y").date().isoformat()
    return None


def main() -> None:
    meta = json.loads((DATA / "meta.json").read_text())
    ver = json.loads((DATA / "verifications.json").read_text())
    run_day = date.fromisoformat(meta.get("olbg_locale_date") or meta["run_started_utc"][:10])

    harvest = DATA / meta.get("harvest_file", "raw/olbg-harvest-20261021.tsv")
    fmt = meta.get("harvest_format", "v1")
    fetched_at = meta.get("harvest_completed_utc", "2026-10-21T05:20:00Z")

    # Sports that the primary harvest did not cover keep their rows from the previous
    # harvest (same OLBG event ids), tagged so the reader can see the older fetch time.
    sources = [(harvest, fmt, fetched_at, run_day, None)]
    prev = meta.get("previous_harvest") or {}
    if prev.get("file"):
        p_day = date.fromisoformat(prev.get("olbg_locale_date") or (prev.get("harvest_completed_utc") or meta["run_started_utc"])[:10])
        sources.append((DATA / prev["file"], prev.get("format", "v1"), prev.get("harvest_completed_utc", ""), p_day,
                        f"carried from the {prev.get('harvest_completed_utc', '')[:16]} harvest: fixture started or rotated off OLBG listing prior to {fetched_at[:16]}Z"))
    # A later-day supplementary capture (read after the primary harvest) may only ADD events the
    # earlier captures did not contain. It never overwrites an existing row's published labels,
    # so an evening re-read cannot silently restate what the midday capture recorded.
    for extra in meta.get("supplementary_harvests", []):
        if extra.get("file"):
            s_day = date.fromisoformat(extra.get("olbg_locale_date") or (extra.get("harvest_completed_utc") or meta["run_started_utc"])[:10])
            sources.append((DATA / extra["file"], extra.get("format", "v2"), extra.get("harvest_completed_utc", ""), s_day,
                            f"supplementary evening capture at {extra.get('harvest_completed_utc', '')}: event not present in earlier captures"))
    for extra in meta.get("previous_harvests_extra", []):
        if extra.get("file"):
            e_day = date.fromisoformat(extra.get("olbg_locale_date") or (extra.get("harvest_completed_utc") or meta["run_started_utc"])[:10])
            sources.append((DATA / extra["file"], extra.get("format", "v1"), extra.get("harvest_completed_utc", ""), e_day,
                            f"carried from the {extra.get('harvest_completed_utc', '')[:16]} harvest: fixture started or rotated off OLBG listing prior to {fetched_at[:16]}Z"))

    rows = []
    missing_url_parts = []
    seen_eids: set[str] = set()
    for harvest, fmt, fetched_at, src_day, carry_note in sources:
        for line in harvest.read_text().splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            parts = line.split("|")
            parts += [""] * (11 - len(parts))
            league_label = ""
            if fmt == "v2":
                # v2 columns: sport|league_label|path_prefix|slug|event_id|date_label|time_label|market|consensus|tips|note
                (sport, league_label, prefix, slug, eid, date_label, time_label,
                 market, consensus, tips, note) = parts[:11]
                pct = ""
            else:
                (sport, prefix, slug, eid, date_label, time_label,
                 market, consensus, tips, pct, note) = parts[:11]

            sport = sport.replace("_", " ").strip()
            sport_id = SPORT_IDS.get(sport)
            if sport_id is None:
                missing_url_parts.append(line)
                continue
            if eid in seen_eids:
                continue  # primary harvest already supplied the fresher live listing row for this event_id
            seen_eids.add(eid)
            if carry_note is not None:
                note = (note + "; " if note else "") + carry_note
            url = f"https://www.olbg.com/betting-tips/{prefix}/{slug}/{sport_id}?event_id={eid}"
            event_name = slug.replace("_", " ")
            # The slug is lossy for "@" events; prefer the human name from the page where known.
            ev = ver["event_verifications"].get(eid, {})
            source_home, source_away = split_teams(event_name)
            if source_away:
                source_away = SUFFIX_RE.sub("", source_away)
            display = ev.get("fixture_name") or event_name
            home = ev.get("home") or source_home
            away = ev.get("away") or source_away
            won, total = parse_tips(tips)
            if market in WIN_MARKETS:
                family = "match_winner"
            elif market in OUTRIGHT_MARKETS:
                family = "outright"
            else:
                family = "other"

            rows.append({
                "id": f"{ID_PREFIX[sport]}-{eid}",
                "sport": sport,
                "olbg_sport_id": sport_id,
                "competition": ev.get("competition") or None,
                "competition_status": competition_status(ev),
                "venue": ev.get("venue") or None,
                "verified_start": ev.get("start_local") or None,
                "event_name": display,
                **({"olbg_event_name": event_name} if display != event_name else {}),
                "home": home,
                "away": away,
                "olbg_date_label": date_label,
                "olbg_time_label": time_label,
                "date_iso": resolve_date(date_label, src_day),
                "olbg_market": market or None,
                "market_family": family,
                "olbg_consensus_selection": consensus or None,
                "olbg_tips": tips or None,
                "olbg_tips_won": won,
                "olbg_tips_total": total,
                "olbg_confidence_pct": int(pct) if pct.strip().isdigit() else None,
                "olbg_url": url,
                "olbg_league_label": league_label or None,
                "verification_status": ev.get("status") or "unverified",
                "verification_note": ev.get("note") or None,
                "official_start_utc": ev.get("start_utc") or None,
                "fetched_at": fetched_at,
                "verification_ids": ev.get("sources", []),
                "ambiguous_exclusion": sport == "Gaelic Football",
                "row_notes": note or None,
            })

    # de-duplicate on the OLBG event id (a fixture may appear twice if two markets were listed)
    seen = {}
    for r in rows:
        key = r["olbg_url"]
        if key in seen:
            seen[key]["duplicate_market"] = seen[key].get("duplicate_market") or []
            seen[key]["duplicate_market"].append(r["olbg_market"])
            continue
        seen[key] = r
    matches = list(seen.values())

    # Live corrections sit on top of the dated harvest files, which are never edited:
    # data/live_overrides.json records what the source says now and why the captured row moved.
    ov_path = DATA / "live_overrides.json"
    ov = json.loads(ov_path.read_text()) if ov_path.exists() else {"withdrawn": [], "updates": []}
    retired = {str(w.get("match_id") or w.get("olbg_event_id")) for w in ov.get("withdrawn", [])}
    if retired:
        before = len(matches)
        matches = [m for m in matches if m["id"] not in retired]
        print(f"retracted: {before - len(matches)} row(s) removed by data/live_overrides.json")
    by_id = {u["match_id"]: u for u in ov.get("updates", []) if u.get("match_id")}
    applied = 0
    for m in matches:
        u = by_id.get(m["id"])
        if not u:
            continue
        if u.get("olbg_consensus_selection"):
            m["olbg_consensus_selection"] = u["olbg_consensus_selection"]
        if u.get("olbg_tips"):
            m["olbg_tips"] = u["olbg_tips"]
            won, total = parse_tips(u["olbg_tips"])
            m["olbg_tips_won"], m["olbg_tips_total"] = won, total
        if u.get("olbg_confidence_pct") is not None:
            m["olbg_confidence_pct"] = u["olbg_confidence_pct"]
        if u.get("row_notes"):
            m["row_notes"] = u["row_notes"]
        applied += 1
    if applied:
        print(f"live overrides applied: {applied}")

    (DATA / "matches.json").write_text(json.dumps(matches, indent=2) + "\n")
    print(f"matches: {len(matches)}  (skipped {len(missing_url_parts)} rows without a sport id)")


if __name__ == "__main__":
    main()
