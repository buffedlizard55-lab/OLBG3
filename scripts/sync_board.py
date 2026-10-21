#!/usr/bin/env python3
"""sync_board.py - translate the OLBG-lines dataset (tools/*) into the board-track inputs.

Reads : data/matches.json, data/lines.json, data/predictions-olbg.json, data/verifications.json,
        data/flagged.json, data/meta.json
Writes: data/events.json, data/predictions.json, data/official.json, data/sports/<slug>.json

The two site tracks used to be fed by two different harvests. From the 06:50Z harvest onward the
root dashboard (scripts/build_site.py) is generated from the same rows, lines and verifications as
the /olbg audit board, so the two can no longer disagree. Nothing is inferred here: every field is
copied from the source files, and a blank stays blank.
"""
from __future__ import annotations

import glob
import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as fh:
        return json.load(fh)


def dump(name, obj):
    path = os.path.join(DATA, name)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def slug_of(sport: str) -> str:
    return sport.lower().replace(" ", "_")


def start_label(m: dict) -> str:
    """OLBG's own label, with the resolved calendar date and the zone we established for it."""
    iso = m.get("date_iso")
    day = date.fromisoformat(iso).strftime("%d %b").lstrip("0") if iso else m["olbg_date_label"]
    return f"{day} {m['olbg_time_label']} EDT".strip()


def main() -> None:
    meta = load("meta.json")
    matches = load("matches.json")
    lines = {l["match_id"]: l for l in load("lines.json")}
    preds = load("predictions-olbg.json")
    ver = load("verifications.json")
    flagged = load("flagged.json")
    src_by_id = {s["id"]: s for s in ver["sources"]}
    evs = ver["event_verifications"]

    events = []
    for m in matches:
        eid = m["id"].split("-", 1)[1]
        ln = lines[m["id"]]
        v = evs.get(eid, {})
        status = m.get("verification_status") or "unverified"
        first_src = next((src_by_id[s] for s in v.get("sources", []) if s in src_by_id), None)
        home = m["home"] or m["event_name"]
        away = m["away"] or ("outright market" if m["market_family"] == "outright" else "")

        # model block: our own prices, carried over exactly as originate.py produced them
        prices, probs = {}, {}
        pick_side = None
        if ln.get("our_pick") and ln.get("our_price_pick") and m["home"] and m["away"]:
            pick_side = "home" if ln["our_pick"] == m["home"] else "away"
            prices["win_home" if pick_side == "home" else "win_away"] = ln["our_price_pick"]
            if ln.get("our_price_other"):
                prices["win_away" if pick_side == "home" else "win_home"] = ln["our_price_other"]
        if ln.get("our_home_probability") is not None:
            probs = {"home": ln["our_home_probability"], "away": round(1 - ln["our_home_probability"], 4)}
        notes = list(ln.get("flags", []))
        if ln.get("our_handicap_line") is not None:
            notes.append(f"our handicap: {ln['our_handicap_side']} {ln['our_handicap_line']:+g} {ln['our_handicap_unit']}")
        if ln.get("our_total_line") is not None:
            notes.append(f"our total: {ln['our_total_line']} {ln['our_total_unit']} ({ln['our_total_basis']})")

        won, tot = m.get("olbg_tips_won"), m.get("olbg_tips_total")
        events.append({
            "ref": m["id"],
            "sport": m["sport"],
            "sport_slug": slug_of(m["sport"]),
            "competition": m.get("competition") or "",
            "olbg_league_label": m.get("olbg_league_label") or "",
            "home": home,
            "away": away,
            "start": start_label(m),
            "olbg_market": m.get("olbg_market") or "",
            "olbg_pick": m.get("olbg_consensus_selection") or "",
            "olbg_tips": m.get("olbg_tips") or "",
            "olbg_pct": round(100 * won / tot) if won is not None and tot else None,
            "olbg_event_url": m["olbg_url"],
            "olbg_event_id": int(eid),
            "olbg_listing_url": f"https://www.olbg.com/betting-tips/{m['olbg_url'].split('/betting-tips/')[1].split('/')[0]}/{m['olbg_sport_id']}",
            "market_family": m["market_family"],
            "verification": {
                "status": status,
                "official_url": first_src["url"] if first_src else "",
                "official_label": first_src["name"] if first_src else "",
                "official_datetime": " / ".join(x for x in [v.get("start_local"), (v.get("start_utc") or "") and f"{v['start_utc']}"] if x),
                "venue": v.get("venue") or "",
                "facts": v.get("facts", []),
                "note": v.get("note") or ("No official source retrieved and confirmed for this fixture in this pass." if status == "unverified" else ""),
            },
            "model": {
                "basis": ln["inputs"]["basis"],
                "prices": prices,
                "probs": probs,
                # prices on handicap/total lines are deliberately absent: originate.py publishes the line only
                "handicap": ({"fav": "home" if ln.get("our_handicap_side") == m["home"] else "away",
                              "line": -abs(ln["our_handicap_line"]), "dog_line": abs(ln["our_handicap_line"]),
                              "unit": ln.get("our_handicap_unit"), "price": None, "dog_price": None}
                             if ln.get("our_handicap_line") is not None and m["home"] and m["away"] else None),
                "total": ({"line": ln["our_total_line"], "unit": ln.get("our_total_unit"), "basis": ln.get("our_total_basis"),
                           "over": None, "under": None}
                          if ln.get("our_total_line") is not None else None),
                "notes": notes,
            },
            "pick": {
                "side": pick_side,
                "label": ln.get("our_pick") or "",
                "prob": ln.get("our_pick_probability"),
                "confidence": ln["confidence"].upper(),
                "score": 0,
                "factors": {
                    "fixture_verified": 1 if status == "verified" else 0,
                    "official_form": 1 if len(v.get("facts", [])) > 1 and status == "verified" else 0,
                    "model_edge": 1 if ln.get("our_pick_probability") and ln["our_pick_probability"] >= 0.58 else 0,
                },
            },
        })

    assumptions = [
        "Match-winner probability = OLBG tip split shrunk with a Beta(2,2) prior, then a sport-level home-field logit shift (tools/originate.py; constants in data/model.md).",
        "Our prices carry a 5% theoretical hold. They are model output, not bookmaker prices and not facts.",
        "Handicap = -(sigma x z) rounded to the half unit, where sigma is the disclosed per-sport margin standard deviation; totals are per-sport baselines.",
        "HIGH confidence is assigned only where a written prediction cites official current-form facts; such picks are priced at no less than 65% (disclosed floor).",
        "OLBG start labels are rendered in US Eastern (UTC-4) for this fetcher; the official UTC time, where confirmed, is in the verification column.",
    ]
    dump("events.json", {"generated": meta.get("harvest_completed_utc", "")[:10], "generated_utc": meta.get("harvest_completed_utc", ""),
                         "harvest": meta.get("harvest_file", ""), "assumptions": assumptions, "events": events})

    # predictions
    out_preds = []
    for p in preds["predictions"]:
        out_preds.append({"ref": p["match_id"], "selection": p["selection"], "headline": p.get("headline") or p["selection"],
                          "body": p["text"], "sources": p["sources"], "word_count": p.get("word_count")})
    dump("predictions.json", {"note": preds.get("note", ""), "generated_at": preds.get("generated_at", ""), "predictions": out_preds})

    # official register (what we confirmed, from where)
    conf = {}
    not_verified = []
    for ev in events:
        if ev["verification"]["status"] == "verified":
            conf[ev["ref"]] = {"status": "verified", "olbg": ev["start"], "official": ev["verification"]["official_datetime"],
                               "venue": ev["verification"]["venue"], "competition": ev["competition"],
                               "source": ev["verification"]["official_url"], "source_label": ev["verification"]["official_label"],
                               "facts": ev["verification"]["facts"], "note": ev["verification"]["note"]}
        else:
            not_verified.append({"ref": ev["ref"], "status": ev["verification"]["status"], "note": ev["verification"]["note"]})
    dump("official.json", {"note": "Only facts copied from official competition sources are stored here, each with the exact source URL. Nothing is inferred.",
                           "retrieved": ver.get("retrieved_at", ""), "sources": ver["sources"], "fixture_confirmations": conf, "not_verified": not_verified})

    # per-sport listing files (one per sport present in the harvest; stale files are removed)
    sport_ids = {m["sport"]: m["olbg_sport_id"] for m in matches}
    olbg_slug = {m["sport"]: m["olbg_url"].split("/betting-tips/")[1].split("/")[0] for m in matches}
    for old in glob.glob(os.path.join(DATA, "sports", "*.json")):
        os.remove(old)
    for sport, sid in sport_ids.items():
        rows = [ev for ev in events if ev["sport"] == sport]
        dump(os.path.join("sports", f"{slug_of(sport)}.json"), {
            "sport": sport, "olbg_slug": olbg_slug[sport], "olbg_id": sid,
            "listing_url": f"https://www.olbg.com/betting-tips/{olbg_slug[sport]}/{sid}",
            "fetched": meta.get("harvest_completed_utc", "")[:10],
            "listing_note": f"{len(rows)} rows rendered server-side on the OLBG listing(s) at 06:45-07:05Z; each list ends in a 'Load More Tips' control the fetcher cannot press, so this is OLBG's first page, not its whole card.",
            "events": [{"ref": ev["ref"], "competition": ev["competition"], "home": ev["home"], "away": ev["away"], "start": ev["start"],
                        "market": ev["olbg_market"], "olbg_pick": ev["olbg_pick"], "tips": ev["olbg_tips"], "pct": ev["olbg_pct"],
                        "event_url": ev["olbg_event_url"], "event_id": ev["olbg_event_id"]} for ev in rows]})

    from collections import Counter
    print("board: events", len(events), Counter(ev["verification"]["status"] for ev in events),
          Counter(ev["pick"]["confidence"] for ev in events), "predictions", len(out_preds), "flagged", len(flagged["items"]))


if __name__ == "__main__":
    main()
