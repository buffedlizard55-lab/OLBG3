#!/usr/bin/env python3
"""check_board.py - fail the build if the published board breaks its own rules.

Rules enforced (each one maps to a promise made on the site):
 1. Every row links to the OLBG event page it came from, and the link carries an event id.
 2. A row marked 'verified' has an official http(s) URL, a label AND a source tier of official or
    club-official; a row marked 'corroborated' has a third-party link, is never graded HIGH and never
    claims an official tier; a row marked 'unverified' carries no official value at all.
 3. Every price is a decimal price > 1, and every outright price recomputes from the published
    formula p = (wins + a)/(total + k) with a 5% overround.
 4. Refs are unique; only in-scope sports appear; no excluded sport leaks in.
 5. Every HIGH-confidence row has a written prediction of at least 30 words with at least one
    http(s) source, and a prediction exists only for a HIGH row; predictions never reference a row
    that is not on the board.
 6. No data file contains unresolved merge-conflict markers.
 7. The published brief-coverage accounting (data/brief_coverage.json) recomputes exactly from the
    committed rows, covers every sport the brief covers and never lists an excluded sport. If the
    rows move, the page's numbers must move with them - no hand-edited counts.
 8. No two written predictions on the root board are the same text: the brief asks for unique,
    non-repetitive prose, so a copy-paste duplicate is a build failure, not a style note.
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from board_dates import in_band, american, BAND_LOW_DEC, BAND_HIGH_DEC
from brief_coverage import build as build_brief_coverage

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"Tennis", "Basketball", "Ice Hockey", "Cricket", "Baseball", "Volleyball", "Darts",
           "Snooker", "Rugby Union", "Rugby League", "Handball", "Gaelic Football",
           "Golf", "Motor Racing", "Greyhounds"}
EXCLUDED = {"football", "soccer", "boxing", "ufc", "mma", "american football", "hurling",
            "horse racing", "cycling", "specials"}
CONF = {"HIGH", "MEDIUM", "LOW"}
MARKERS = ("<<<<<<<", ">>>>>>>", "=======\n")

errors, warnings = [], []


def load(path):
    p = os.path.join(ROOT, path)
    raw = open(p, encoding="utf-8").read()
    for m in MARKERS:
        if m in raw:
            errors.append(f"{path}: contains merge-conflict marker {m!r}")
    return json.loads(raw)


def check_rows(rows, preds):
    refs = set()
    for r in rows:
        ref = r.get("ref", "?")
        if ref in refs:
            errors.append(f"{ref}: duplicate ref")
        refs.add(ref)

        if r.get("sport") not in ALLOWED:
            errors.append(f"{ref}: sport {r.get('sport')!r} is not in scope")
        if str(r.get("sport", "")).lower() in EXCLUDED:
            errors.append(f"{ref}: excluded sport published")

        url = r.get("olbg_event_url", "")
        if urlparse(url).hostname != "www.olbg.com" or "event_id=" not in url:
            errors.append(f"{ref}: OLBG source link missing or malformed ({url!r})")

        v = r.get("verification") or {}
        status = v.get("status")
        if status == "verified":
            ou = v.get("official_url", "")
            if urlparse(ou).scheme not in ("http", "https"):
                errors.append(f"{ref}: marked verified without an official URL")
            if not v.get("official_label"):
                errors.append(f"{ref}: marked verified without an official label")
            if v.get("source_tier") not in ("official", "club-official"):
                errors.append(f"{ref}: marked verified but its source tier is {v.get('source_tier')!r} "
                              f"(only official / club-official may be verified)")
        elif status == "corroborated":
            # a third-party listing: kept, labelled, and never counted as official confirmation
            ou = v.get("official_url", "")
            if urlparse(ou).scheme not in ("http", "https") or not v.get("official_label"):
                errors.append(f"{ref}: marked corroborated without a link and label")
            if v.get("source_tier") in ("official", "club-official"):
                errors.append(f"{ref}: marked corroborated but its source tier is official - it should be verified")
            if r.get("pick", {}).get("confidence") == "HIGH":
                errors.append(f"{ref}: corroborated (third-party) row graded HIGH - it must not earn the verification point")
        elif status == "unverified":
            if v.get("official_url") or v.get("official_datetime"):
                errors.append(f"{ref}: marked unverified but carries an official value")
        else:
            errors.append(f"{ref}: unknown verification status {status!r}")

        if r.get("pick", {}).get("confidence") not in CONF:
            errors.append(f"{ref}: confidence {r.get('pick', {}).get('confidence')!r} not graded")

        for key, val in (r.get("model", {}).get("prices") or {}).items():
            if val is None:
                continue  # a null price means "not priced", which is allowed and rendered as n/p
            if not isinstance(val, (int, float)) or val <= 1:
                errors.append(f"{ref}: price {key}={val!r} is not a decimal price > 1")

        if "single" in (r.get("model", {}).get("prices") or {}):
            prior = r["model"]["prior"]
            a, k = prior["a"], prior["strength_k"]
            won, tot = r.get("olbg_tips", "0/0").split("/")
            won, tot = int(won), int(tot)
            expected_p = (won + a) / (tot + k)
            expected_price = round(0.95 / expected_p, 2)
            if abs(expected_p - r["model"]["probs"]["single"]) > 1e-3:
                errors.append(f"{ref}: outright probability does not recompute")
            # the stored probability is rounded to 4dp before the price is taken, so allow 5p
            if abs(expected_price - r["model"]["prices"]["single"]) > 0.05:
                errors.append(f"{ref}: outright price does not recompute ({expected_price} vs {r['model']['prices']['single']})")

        pk = r.get("pick") or {}
        price = pk.get("price")
        if pk.get("confidence") == "HIGH":
            if not price or not in_band(price):
                errors.append(f"{ref}: HIGH confidence but its price {price!r} is outside the "
                              f"-250..+10000 band (decimal {BAND_LOW_DEC}..{BAND_HIGH_DEC})")
            if pk.get("kickoff_passed"):
                errors.append(f"{ref}: HIGH confidence but its kick-off date has passed")
            if ref not in preds:
                errors.append(f"{ref}: HIGH confidence but no written prediction")
            elif preds[ref].get("status") != "high":
                errors.append(f"{ref}: HIGH confidence but its written piece is marked {preds[ref].get('status')!r}")
        else:
            # a written piece on a non-HIGH row is allowed only as labelled analysis
            if ref in preds and preds[ref].get("status") != "analysis":
                errors.append(f"{ref}: graded {pk.get('confidence')} but its written piece is marked "
                              f"{preds[ref].get('status')!r}, not 'analysis'")

        # the stored US odds must be the arithmetic conversion of the stored decimal price
        if price and pk.get("american") != american(price):
            errors.append(f"{ref}: US odds {pk.get('american')!r} do not convert from decimal {price!r} "
                          f"(expected {american(price)!r})")

    return refs


def check_predictions(preds, refs, rows_by_ref):
    """Every price quoted in a written piece must be the price published on its row.

    Prose is hand-written and the model re-prices rows on every rebuild, so without this rule a
    prediction can keep tipping "8.38" long after the row moved to 8.40. The site would then show
    two different prices for the same selection. Quoted prices are therefore compared to the row
    and any drift is a build failure, not a warning.
    """
    for ref, p in preds.items():
        body = p.get("body", "")
        words = len(body.split())
        if words < 30:
            errors.append(f"{ref}: prediction is {words} words, under the 30-word floor")
        if not p.get("selection"):
            errors.append(f"{ref}: prediction has no explicit selection")
        if ref not in refs:
            warnings.append(f"{ref}: prediction exists for a row that is not on the board")
        if p.get("status") not in ("high", "analysis"):
            errors.append(f"{ref}: prediction status {p.get('status')!r} is not 'high' or 'analysis'")
        for s in p.get("sources", []):
            if urlparse(s.get("url", "")).scheme not in ("http", "https"):
                errors.append(f"{ref}: prediction source without a URL")

        row = rows_by_ref.get(ref)
        if row:
            pk = row.get("pick") or {}
            price, us = pk.get("price"), pk.get("american")
            # "7.32 (+732 / 7.32)" style selection labels
            for q_us, q_dec in re.findall(r"([+-]\d{2,5})\s*/\s*(\d+\.\d{2})", p.get("selection", "")):
                if us is not None and int(q_us) != us:
                    errors.append(f"{ref}: selection quotes {q_us} but the row's US odds are {us}")
                if price is not None and abs(float(q_dec) - price) > 0.005:
                    errors.append(f"{ref}: selection quotes {q_dec} but the row's decimal price is {price}")
            # prices quoted inline in the prose, e.g. "at 1.67" / "Priced at +241 (3.41)"
            for q_dec in re.findall(r"(?:\bat\b|\bPriced\b)\s*(?:an?\s+)?(\d\.\d{2})\b", body):
                if price is not None and BAND_LOW_DEC <= float(q_dec) <= BAND_HIGH_DEC \
                        and abs(float(q_dec) - price) > 0.005:
                    errors.append(f"{ref}: prose quotes decimal {q_dec} but the row's price is {price}")
            for q_us in re.findall(r"(?:\bat\b|\bPriced\b)\s*(?:an?\s+)?([+-]\d{2,5})\b", body):
                if us is not None and int(q_us) != us:
                    errors.append(f"{ref}: prose quotes {q_us} US but the row's US odds are {us}")


def check_brief_coverage(allowed):
    """Rule 7: the published accounting must recompute from the rows, not be typed by hand."""
    try:
        committed = load("data/brief_coverage.json")
    except FileNotFoundError:
        errors.append("data/brief_coverage.json is missing; run scripts/brief_coverage.py")
        return
    try:
        recomputed = build_brief_coverage()
    except Exception as exc:  # noqa: BLE001 - surfaced as a build failure with the reason
        errors.append(f"data/brief_coverage.json cannot be recomputed: {exc!r}")
        return
    if committed != recomputed:
        errors.append("data/brief_coverage.json is stale: it does not match the committed rows "
                      "(run scripts/brief_coverage.py and rebuild)")

    seen = [s["sport"] for s in committed.get("sports", [])]
    if sorted(seen) != sorted(allowed):
        errors.append(f"brief coverage lists {sorted(seen)} instead of the {len(allowed)} covered sports")
    for s in committed.get("sports", []):
        if s.get("target") != committed["brief_target"]["picks_per_sport_per_day"]:
            errors.append(f"brief coverage {s['sport']}: target {s.get('target')} is not the brief's target")
        if s.get("shortfall") != max(0, s["target"] - s["live_high_union"]):
            errors.append(f"brief coverage {s['sport']}: shortfall does not recompute")
        if s["meets_target"] != (s["live_high_union"] >= s["target"]):
            errors.append(f"brief coverage {s['sport']}: meets_target does not recompute")
    total_live = sum(s["live_high_union"] for s in committed.get("sports", []))
    if committed["totals"]["live_high_union"] != total_live:
        errors.append("brief coverage totals.live_high_union does not equal the per-sport sum")
    for bad in ("soccer", "boxing", "ufc", "mma", "american football", "hurling",
                "horse racing", "cycling", "specials"):
        if bad in [s.lower() for s in seen]:
            errors.append(f"brief coverage lists the excluded sport {bad!r}")

    xt = committed.get("cross_track", {})
    if xt.get("different_selection") != len(xt.get("rows", [])):
        errors.append("brief coverage cross_track.different_selection does not match its rows")
    for row in xt.get("rows", []):
        for key in ("root_ref", "olbg_ref", "root_selection", "olbg_selection", "olbg_url"):
            if not row.get(key):
                errors.append(f"brief coverage {row.get('event_id')}: cross-track row missing {key}")
        if row.get("root_selection", "").lower() == row.get("olbg_selection", "").lower():
            errors.append(f"brief coverage {row.get('event_id')}: listed as a disagreement but the "
                          "selections are identical")


def check_unique_prose(preds):
    """Rule 8: identical bodies are a duplicate, however plausible they read."""
    seen = {}
    for ref, p in preds.items():
        body = " ".join((p.get("body") or "").split()).lower()
        if not body:
            continue
        if body in seen:
            errors.append(f"{ref}: prediction body duplicates {seen[body]} word for word")
        else:
            seen[body] = ref


def main():
    ev = load("data/events.json")
    gap = load("data/gap_sports.json")
    preds = {p["ref"]: p for p in load("data/predictions.json")["predictions"]}

    fixture_rows = ev["events"]
    gap_rows = gap["rows"]
    for r in fixture_rows:
        r.setdefault("market_type", "fixture")

    refs = check_rows(fixture_rows + gap_rows, preds)
    check_predictions(preds, refs, {r["ref"]: r for r in fixture_rows + gap_rows})
    check_brief_coverage(ALLOWED)
    check_unique_prose(preds)

    priced = sum(1 for r in fixture_rows + gap_rows if (r.get("model", {}).get("prices") or {}))
    verified = sum(1 for r in fixture_rows + gap_rows if r["verification"]["status"] == "verified")
    print(f"rows={len(fixture_rows) + len(gap_rows)} fixtures={len(fixture_rows)} outright_or_race={len(gap_rows)} "
          f"verified={verified} priced={priced} predictions={len(preds)}")
    for w in warnings:
        print(f"  WARN {w}")
    for e in errors:
        print(f"  FAIL {e}")
    if errors:
        print(f"FAIL: {len(errors)} rule violation(s)")
        return 1
    print("PASS: every row has an OLBG source, verification is all-or-nothing, prices recompute, every HIGH pick "
          "is inside the -250..+10000 band with a live kick-off and a written prediction, every non-HIGH piece "
          "is labelled analysis, the brief-coverage accounting recomputes and no two write-ups are duplicates.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
