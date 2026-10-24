#!/usr/bin/env python3
"""exec_summary.py - one merged, de-duplicated answer to "what is the pick, and where is it?"

Why this exists
---------------
The repository carries two independent line-origination pipelines (the root board in
`data/events.json` + `data/gap_sports.json`, and the `/olbg/` audit track in
`data/lines.json`) and ~20 published pages. A reader arriving at the site could not tell
which page held today's selections. This script produces *one* list, merged across both
tracks and de-duplicated on the OLBG event id, of every selection that is currently
releasable as a HIGH-confidence pick, plus a clearly-labelled watchlist row per sport so
that no covered sport looks silently empty.

What it does NOT do
-------------------
* It fetches nothing. Every value is copied from a committed pipeline output.
* It grades nothing and upgrades nothing. A row is HIGH here only if the pipeline that
  produced it already decided HIGH *and* its own release object says `status == "upcoming"`.
* It does not renew any checked_at, clock or price. The publication clock is read from
  `data/publication.json` and is displayed, not used to promote anything.
* It never fills a blank: a missing source, write-up or start is carried through as null
  and rendered as blank + flagged.

Output: data/exec_summary.json (consumed by scripts/build_site.py -> summary.html and
the landing page; validated by scripts/check_exec_summary.py).
"""
from __future__ import annotations

import datetime as dt
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

SPORTS = ["Tennis", "Basketball", "Ice Hockey", "Cricket", "Baseball", "Volleyball", "Darts",
          "Snooker", "Rugby Union", "Rugby League", "Handball", "Gaelic Football",
          "Golf", "Motor Racing", "Greyhounds"]

SLUG = {
    "Cricket": "cricket", "Tennis": "tennis", "Basketball": "basketball",
    "Snooker": "snooker", "Darts": "darts", "Rugby Union": "rugby_union",
    "Rugby League": "rugby_league", "Ice Hockey": "ice_hockey", "Baseball": "baseball",
    "Volleyball": "volleyball", "Handball": "handball", "Golf": "golf",
    "Motor Racing": "motor_racing", "Gaelic Football": "gaelic_football",
    "Greyhounds": "greyhounds",
}

# Why a priced row is not a released pick. Single source of wording so the summary page,
# the sport pages and the checker cannot drift apart.
GATE_REASON = {
    "unverified_start": "the start has no timezone-qualified official clock, so it cannot be released",
    "past_date": "the recorded date has passed, so the row is archive only",
    "start_window_reached": "the scheduled start has passed at this publication clock",
    "stale_source": "the official observation behind it is older than 24 hours",
    "source_conflict": "the official source and the capture disagree, so the selection is held",
}


def load(name, default=None):
    p = DATA / name
    if not p.exists():
        return default
    return json.loads(p.read_text())


def clock():
    stamp = load("publication.json")["publication_as_of"]
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def words(text):
    return len(re.findall(r"[A-Za-z0-9'’\-]+", text or ""))


def label_utc(iso):
    if not iso:
        return None
    moment = dt.datetime.fromisoformat(iso.replace("Z", "+00:00")).astimezone(dt.timezone.utc)
    return moment.strftime("%a %d %b, %H:%M UTC")


def event_key(value):
    """Every OLBG event id in this repo is the trailing digits of a ref or match_id."""
    m = re.search(r"(\d+)$", str(value or ""))
    return int(m.group(1)) if m else None


def price_of_root(row):
    pick = row.get("pick") or {}
    if pick.get("price") is not None:
        return pick["price"]
    prices = (row.get("model") or {}).get("prices") or {}
    if pick.get("side") == "home":
        return prices.get("win_home")
    if pick.get("side") == "away":
        return prices.get("win_away")
    return prices.get("single")


def american(price):
    if not price:
        return None
    if price >= 2.0:
        return f"+{round((price - 1) * 100)}"
    return f"{round(-100 / (price - 1))}"


def prediction_index():
    """Root write-ups keyed by ref, and /olbg/ write-ups keyed by match_id."""
    root = {p["ref"]: p for p in (load("predictions.json", {}) or {}).get("predictions", [])}
    olbg = {p["match_id"]: p for p in (load("predictions-olbg.json", {}) or {}).get("predictions", [])}
    return root, olbg


def sources_of(piece):
    out = []
    for item in (piece or {}).get("sources") or []:
        if isinstance(item, dict) and item.get("url"):
            out.append({"label": item.get("label") or item["url"], "url": item["url"]})
        elif isinstance(item, str) and item.startswith("http"):
            out.append({"label": item, "url": item})
    return out


def merged_rows():
    """One dict per OLBG event, from both tracks. Nothing is added that a track did not say."""
    root_preds, olbg_preds = prediction_index()
    events = load("events.json")["events"] + load("gap_sports.json")["rows"]
    lines = load("lines.json")

    merged = {}

    def slot(key, sport, label):
        row = merged.setdefault(key, {"sport": sport, "olbg_event_id": key, "tracks": {},
                                      "writeups": [], "sources": []})
        row.setdefault("event_name", label)
        return row

    for r in events:
        key = r.get("olbg_event_id") or event_key(r.get("ref"))
        if not key:
            continue
        pick = r.get("pick") or {}
        rel = pick.get("release") or {}
        name = (f"{r['away']} @ {r['home']}" if r.get("away") and r.get("home")
                else (r.get("home") or ""))
        row = slot(key, r["sport"], name)
        row["event_name"] = name if not row.get("event_name") else row["event_name"]
        row["competition"] = row.get("competition") or r.get("competition")
        price = price_of_root(r)
        piece = root_preds.get(r.get("ref"))
        if piece:
            body = piece.get("text") or piece.get("body")
            row["writeups"].append({"track": "root", "ref": r["ref"], "text": body,
                                    "words": words(body), "confidence": piece.get("confidence"),
                                    "selection": piece.get("selection"), "headline": piece.get("headline")})
            for s in sources_of(piece):
                if s not in row["sources"]:
                    row["sources"].append(s)
        row["tracks"]["root"] = {
            "ref": r.get("ref"), "sport": r["sport"], "selection": pick.get("label"),
            "market": r.get("olbg_market"), "price": price,
            "us": pick.get("american") or american(price),
            "prob": pick.get("prob"), "confidence": pick.get("confidence"),
            "release_status": rel.get("status"), "start_utc": rel.get("start_utc"),
            "expires_at": rel.get("expires_at"), "checked_at": rel.get("checked_at"),
            "source": rel.get("source"),
            "official_url": (r.get("verification") or {}).get("official_url"),
            "official_label": (r.get("verification") or {}).get("official_label"),
            "verification_status": (r.get("verification") or {}).get("status"),
            "market_type": r.get("market_type", "fixture"),
            "page": f"../sports/{SLUG.get(r['sport'], '')}.html#row-{r.get('ref')}",
        }
        row["start_utc"] = row.get("start_utc") or rel.get("start_utc")

    for l in lines:
        key = event_key(l.get("match_id"))
        if not key:
            continue
        rel = l.get("release") or {}
        row = slot(key, l["sport"], l.get("event_name"))
        row["event_name"] = l.get("event_name") or row.get("event_name")
        row["competition"] = row.get("competition") or l.get("competition")
        piece = olbg_preds.get(l.get("match_id"))
        if piece:
            body = piece.get("text") or piece.get("body")
            row["writeups"].append({"track": "olbg", "ref": l["match_id"], "text": body,
                                    "words": words(body), "confidence": piece.get("confidence"),
                                    "selection": piece.get("selection"), "headline": piece.get("headline")})
            for s in sources_of(piece):
                if s not in row["sources"]:
                    row["sources"].append(s)
        row["tracks"]["olbg"] = {
            "ref": l.get("match_id"), "sport": l["sport"], "selection": l.get("our_pick"),
            "market": (l.get("inputs") or {}).get("olbg_market"),
            "price": l.get("our_price_pick"),
            "us": l.get("our_us_odds_pick") or american(l.get("our_price_pick")),
            "prob": l.get("our_pick_probability"), "confidence": (l.get("confidence") or "").upper() or None,
            "release_status": rel.get("status"), "start_utc": rel.get("start_utc"),
            "expires_at": rel.get("expires_at"), "checked_at": rel.get("checked_at"),
            "source": rel.get("source"),
            "official_url": None, "official_label": None,
            "verification_status": None,
            "market_type": "fixture",
            "page": "../olbg/picks.html",
            "handicap": {"line": l.get("our_handicap_line"), "side": l.get("our_handicap_side"),
                         "unit": l.get("our_handicap_unit")},
            "total": {"line": l.get("our_total_line"), "side": l.get("our_total_side"),
                      "unit": l.get("our_total_unit")},
        }
        row["start_utc"] = row.get("start_utc") or rel.get("start_utc")
        for k in ("official_url", "official_label", "verification_status"):
            if row["tracks"]["olbg"].get(k):
                row[k] = row["tracks"]["olbg"][k]
    return merged


def is_live_high(view):
    return (view.get("confidence") == "HIGH" and view.get("release_status") == "upcoming"
            and view.get("selection") and view.get("price"))


def two_sided_band(price):
    return price is not None and 1.40 <= price <= 101.0


def build():
    moment = clock()
    today = moment.date()
    merged = merged_rows()

    picks, watchlist = [], []
    per_sport = {s: {"sport": s, "slug": SLUG[s], "events": 0, "upcoming": 0, "priced": 0,
                     "high": 0, "today_events": 0, "next": None, "high_ids": []} for s in SPORTS}

    for key, row in merged.items():
        sport = row["sport"]
        if sport in per_sport:
            per_sport[sport]["events"] += 1
        live = [(t, v) for t, v in row["tracks"].items() if is_live_high(v)]
        if live:
            live.sort(key=lambda tv: (0 if tv[0] == "root" else 1))
            track, view = live[0]
            start = row.get("start_utc") or view.get("start_utc")
            piece = next((w for w in row["writeups"] if w["track"] == track), None)
            if piece is None and row["writeups"]:
                piece = row["writeups"][0]
            picks.append({
                "id": f"{sport[:3].upper()}-{key}",
                "sport": sport, "slug": SLUG[sport],
                "match": row.get("event_name"), "competition": row.get("competition"),
                "start_utc": start, "start_label": label_utc(start),
                "selection": view["selection"], "market": view.get("market"),
                "price": view.get("price"), "us": view.get("us"),
                "probability_pct": round((view.get("prob") or 0) * 100, 1) if view.get("prob") else None,
                "confidence": "HIGH",
                "in_band": two_sided_band(view.get("price")),
                "writeup": ({"text": piece["text"], "words": piece["words"], "track": piece["track"],
                             "ref": piece["ref"], "selection": piece.get("selection"),
                             "headline": piece.get("headline")} if piece and piece.get("text") else None),
                "sources": row["sources"],
                "official_url": view.get("official_url"), "official_label": view.get("official_label"),
                "verification_status": view.get("verification_status"),
                "tracks": [{"track": t, "ref": v["ref"], "page": v["page"]} for t, v in sorted(row["tracks"].items())],
                "also_published": [{"track": t, "ref": v["ref"], "selection": v["selection"],
                                    "price": v.get("price"), "page": v["page"]}
                                   for t, v in sorted(row["tracks"].items()) if t != track],
            })
            per_sport[sport]["high"] += 1
            per_sport[sport]["high_ids"].append(key)

        for track, view in row["tracks"].items():
            start = row.get("start_utc") or view.get("start_utc")
            upcoming = view.get("release_status") == "upcoming"
            if sport in per_sport:
                if upcoming:
                    per_sport[sport]["upcoming"] += 1
                if view.get("price"):
                    per_sport[sport]["priced"] += 1
                if start and start[:10] == today.isoformat():
                    per_sport[sport]["today_events"] += 1
            if upcoming and view.get("price") and not is_live_high(view) and sport in per_sport:
                if per_sport[sport]["next"] is None or (start or "9999") < (per_sport[sport]["next"] or {}).get("start_utc", "9999"):
                    per_sport[sport]["next"] = {
                        "match": row.get("event_name"), "start_utc": start,
                        "start_label": label_utc(start), "selection": view.get("selection"),
                        "market": view.get("market"), "price": view.get("price"),
                        "us": view.get("us"), "confidence": view.get("confidence"),
                        "hold_reason": GATE_REASON.get(view.get("release_status"), "not released as a pick"),
                        "track": track, "page": view["page"], "ref": view.get("ref"),
                    }

    picks.sort(key=lambda p: (p["start_utc"] or "9999", SPORTS.index(p["sport"]) if p["sport"] in SPORTS else 99))
    for p in picks:
        if not p["start_utc"]:
            watchlist.append(p)

    upcoming_window = (today + dt.timedelta(days=7)).isoformat()
    todays = [p for p in picks if (p["start_utc"] or "")[:10] == today.isoformat()]
    upcoming = [p for p in picks if today.isoformat() < (p["start_utc"] or "9")[:10] <= upcoming_window]
    later = [p for p in picks if (p["start_utc"] or "")[:10] > upcoming_window]

    sports_out = []
    for sport in SPORTS:
        info = per_sport[sport]
        sports_out.append({
            "sport": sport, "slug": info["slug"],
            "events": info["events"], "upcoming": info["upcoming"], "priced": info["priced"],
            "high": info["high"], "today_events": info["today_events"],
            "next": info["next"],
            "meets_target": info["high"] >= 5,
            "shortfall": max(0, 5 - info["high"]),
        })

    doc = {
        "generated_utc": moment.isoformat().replace("+00:00", "Z"),
        "publication_clock": moment.isoformat().replace("+00:00", "Z"),
        "today_utc": today.isoformat(),
        "window_end_utc": upcoming_window,
        "note": ("Merged from data/events.json, data/gap_sports.json, data/lines.json and the two prediction "
                 "files. A row is a pick only when its own pipeline graded it HIGH and its own release object "
                 "says upcoming. Nothing was fetched, re-graded or renewed by this build; blank means unknown."),
        "counts": {
            "picks_high": len(picks),
            "picks_today": len(todays),
            "picks_next_7_days": len(upcoming),
            "picks_later": len(later),
            "picks_without_start": len([p for p in picks if not p["start_utc"]]),
            "sports_covered": len([s for s in sports_out if s["events"]]),
            "sports_with_a_pick": len([s for s in sports_out if s["high"]]),
            "sports_meeting_five": len([s for s in sports_out if s["meets_target"]]),
            "events_merged": len(merged),
            "events_today": len({k for k, r in merged.items()
                                 if any((v.get("start_utc") or "")[:10] == today.isoformat()
                                        for v in r["tracks"].values())}),
        },
        "picks": picks,
        "today": todays,
        "next_7_days": upcoming,
        "later": later,
        "sports": sports_out,
    }
    return doc


def main():
    doc = build()
    (DATA / "exec_summary.json").write_text(json.dumps(doc, indent=1) + "\n")
    c = doc["counts"]
    print(f"exec summary: {c['picks_high']} live HIGH picks "
          f"({c['picks_today']} today, {c['picks_next_7_days']} in the next 7 days, "
          f"{c['picks_later']} later) across {c['sports_with_a_pick']} sports; "
          f"{c['events_merged']} events merged, {c['events_today']} dated today.")


if __name__ == "__main__":
    main()
