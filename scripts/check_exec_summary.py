#!/usr/bin/env python3
"""check_exec_summary.py - structural gate for data/exec_summary.json and its two pages.

The executive summary is the page a reader is told to start from, so it is also the page
where a wrong number would do the most damage. Everything it states is recomputed here
from the same committed files it was built from:

  * the counts are re-derived from the lists they describe (never trusted as stored);
  * every published pick must still be HIGH, released `upcoming`, priced inside the
    -250 / +10000 band, carry a start, a source and a write-up of at least 30 words;
  * the write-up must be traceable to the prediction file it claims to come from,
    must not be duplicated, and must not contain the two words the brief bans;
  * the pick list must be sorted, partitioned (today / next seven days / later) and
    de-duplicated on the OLBG event id;
  * the per-sport table must cover all fifteen sports and agree with the pick list.

It reads only committed files. It fetches nothing, so a PASS means "the summary agrees
with the data", not "the data is true" - the latter is what the per-row sources are for.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
sys.path.insert(0, str(ROOT / "scripts"))

import exec_summary  # noqa: E402

BANNED = re.compile(r"\b(model|verified)\b", re.I)
MIN_WORDS = 30
BAND = (1.40, 101.0)


def load(name):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def _us(value):
    """US odds are written with or without a leading '+' by the two pipelines; compare the number."""
    text = value.strip().replace("−", "-")
    return int(text.lstrip("+")) if text.lstrip("+").isdigit() else int(text)


def american_from(price):
    if price >= 2.0:
        return f"+{round((price - 1) * 100)}"
    return f"{round(-100 / (price - 1))}"


def main() -> int:
    errors: list[str] = []
    doc = load("exec_summary.json")
    lines = {r["match_id"]: r for r in load("lines.json")}
    root_preds = {p["ref"]: p for p in (load("predictions.json").get("predictions") or [])}
    olbg_preds = {p["match_id"]: p for p in load("predictions-olbg.json")["predictions"]}
    matches = {m["id"]: m for m in load("matches.json")}

    picks = doc["picks"]
    counts = doc["counts"]
    today = doc["today_utc"]
    window_end = doc["window_end_utc"]

    # 1. Counts are re-derived, not trusted.
    todays = [p for p in picks if (p.get("start_utc") or "")[:10] == today]
    nxt = [p for p in picks if today < (p.get("start_utc") or "9")[:10] <= window_end]
    later = [p for p in picks if (p.get("start_utc") or "")[:10] > window_end]
    for key, value in (("picks_high", len(picks)), ("picks_today", len(todays)),
                       ("picks_next_7_days", len(nxt)), ("picks_later", len(later))):
        if counts.get(key) != value:
            errors.append(f"{key}: stored {counts.get(key)} != recomputed {value}")
    if len(todays) + len(nxt) + len(later) != len(picks):
        errors.append("today + next 7 days + later does not cover every pick")

    # 2. Every pick must still pass every gate, and be traceable to a committed row.
    for p in picks:
        tag = f"{p.get('id')} ({p.get('match')})"
        if p.get("confidence") != "HIGH":
            errors.append(f"{tag}: published with confidence {p.get('confidence')!r}")
        if not p.get("start_utc"):
            errors.append(f"{tag}: no start_utc")
        price = p.get("price")
        if not isinstance(price, (int, float)):
            errors.append(f"{tag}: no price")
        elif not BAND[0] <= price <= BAND[1]:
            errors.append(f"{tag}: price {price} outside {BAND}")
        elif p.get("us") is not None and _us(str(p["us"])) != _us(american_from(price)):
            errors.append(f"{tag}: US odds {p['us']!r} != {american_from(price)} implied by {price}")
        if not p.get("in_band"):
            errors.append(f"{tag}: in_band false but published")
        if not p.get("sources"):
            errors.append(f"{tag}: no source link")
        if not p.get("selection"):
            errors.append(f"{tag}: no selection")

        ref = (p.get("tracks") or [{}])[0].get("ref") or ""
        row = lines.get(ref)
        if row is None:
            errors.append(f"{tag}: track ref {ref!r} is not in data/lines.json")
            continue
        if (row.get("release") or {}).get("status") != "upcoming":
            errors.append(f"{tag}: row release is {(row.get('release') or {}).get('status')!r}, not upcoming")
        if row.get("confidence") != "high":
            errors.append(f"{tag}: row is graded {row.get('confidence')!r}, not high")
        if p.get("price") != row.get("our_price_pick"):
            errors.append(f"{tag}: summary price {p.get('price')} != row price {row.get('our_price_pick')}")

        w = p.get("writeup") or {}
        if not w.get("text"):
            errors.append(f"{tag}: published without a written prediction")
            continue
        if w["words"] < MIN_WORDS:
            errors.append(f"{tag}: write-up is {w['words']} words, under {MIN_WORDS}")
        if re.findall(r"[A-Za-z0-9'’\-]+", w["text"]) and \
                len(re.findall(r"[A-Za-z0-9'’\-]+", w["text"])) != w["words"]:
            errors.append(f"{tag}: stored word count does not recompute")
        if BANNED.search(w["text"]):
            errors.append(f"{tag}: write-up contains a banned word ({BANNED.search(w['text']).group(0)})")
        source = root_preds if w.get("track") == "root" else olbg_preds
        piece = source.get(w.get("ref"))
        if piece is None:
            errors.append(f"{tag}: write-up ref {w.get('ref')!r} not in the {w.get('track')} prediction file")
        elif (piece.get("text") or piece.get("body")) != w["text"]:
            errors.append(f"{tag}: published write-up differs from the stored prediction")
        if len(w["text"].split()) < 30:
            errors.append(f"{tag}: write-up has fewer than 30 whitespace-separated words")
        if row["match_id"] not in olbg_preds and w.get("track") == "olbg":
            errors.append(f"{tag}: /olbg/ write-up missing from data/predictions-olbg.json")
        if row["match_id"] in matches and not matches[row["match_id"]].get("olbg_url"):
            errors.append(f"{tag}: the row has no OLBG listing URL")

    # 3. No fixture twice, no write-up twice, and the ordering is the one the page claims.
    ids = [p.get("id") for p in picks]
    if len(ids) != len(set(ids)):
        errors.append("the same fixture id appears twice")
    texts = [((p.get("writeup") or {}).get("text") or "") for p in picks]
    dupes = {t for t in texts if t and texts.count(t) > 1}
    if dupes:
        errors.append(f"{len(dupes)} write-up(s) are published more than once")
    starts = [p.get("start_utc") or "9999" for p in picks]
    if starts != sorted(starts):
        errors.append("picks are not sorted by start time")

    # 4. The per-sport position must agree with the pick list, for all fifteen sports.
    if len(doc["sports"]) != len(exec_summary.SPORTS):
        errors.append(f"per-sport table has {len(doc['sports'])} sports, expected {len(exec_summary.SPORTS)}")
    for info in doc["sports"]:
        actual = len([p for p in picks if p.get("sport") == info["sport"]])
        if info["high"] != actual:
            errors.append(f"{info['sport']}: table says {info['high']} picks, list has {actual}")
        if info["meets_target"] != (actual >= 5):
            errors.append(f"{info['sport']}: meets_target={info['meets_target']} with {actual} picks")
        if info["shortfall"] != max(0, 5 - actual):
            errors.append(f"{info['sport']}: shortfall {info['shortfall']} does not match {actual} picks")
        nxt_row = info.get("next")
        if nxt_row and nxt_row.get("price") and not BAND[0] <= nxt_row["price"] <= BAND[1]:
            errors.append(f"{info['sport']}: 'next' row price {nxt_row['price']} is outside the band it claims")
        if nxt_row and not nxt_row.get("start_utc"):
            errors.append(f"{info['sport']}: 'next' row has no start")

    # 5. The document must not claim a fresh observation it cannot support.
    if not doc.get("publication_clock"):
        errors.append("no publication clock recorded")
    clock = doc["publication_clock"][:10]
    if doc["today_utc"] != clock:
        errors.append(f"today_utc {doc['today_utc']} is not the publication day {clock}")

    if errors:
        print(f"FAIL: {len(errors)} problem(s) in data/exec_summary.json")
        for e in errors[:40]:
            print("  -", e)
        return 1
    print(f"PASS: {len(picks)} published picks ({len(todays)} today, {len(nxt)} next 7 days, "
          f"{len(later)} later) agree with data/lines.json, the prediction files and the "
          f"per-sport table; {counts['sports_with_a_pick']} of {len(exec_summary.SPORTS)} sports carry a pick.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
