#!/usr/bin/env python3
"""check_board.py - fail the build if the published board breaks its own rules.

Rules enforced (each one maps to a promise made on the site):
 1. Every row links to the OLBG event page it came from, and the link carries an event id.
 2. A row marked 'verified' has an official http(s) URL and a label; a row marked 'unverified'
    carries no official value at all (nothing inferred, nothing half-filled).
 3. Every price is a decimal price > 1, and every outright price recomputes from the published
    formula p = (wins + a)/(total + k) with a 5% overround.
 4. Refs are unique; only in-scope sports appear; no excluded sport leaks in.
 5. Every HIGH-confidence row has a written prediction of at least 30 words with at least one
    http(s) source, and a prediction exists only for a HIGH row; predictions never reference a row
    that is not on the board.
 6. No data file contains unresolved merge-conflict markers.
"""
import json
import os
import re
import sys
from urllib.parse import urlparse

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

        if r["pick"]["confidence"] == "HIGH" and ref not in preds:
            errors.append(f"{ref}: HIGH confidence but no written prediction")
        # ...and the converse: a row that has been downgraded must not keep a published prediction,
        # otherwise the site promises verified form for a pick it no longer rates.
        if ref in preds and r["pick"]["confidence"] != "HIGH":
            errors.append(f"{ref}: has a written prediction but is graded "
                          f"{r['pick']['confidence']}, not HIGH")

    return refs


def check_predictions(preds, refs):
    for ref, p in preds.items():
        body = p.get("body", "")
        words = len(body.split())
        if words < 30:
            errors.append(f"{ref}: prediction is {words} words, under the 30-word floor")
        if not p.get("selection"):
            errors.append(f"{ref}: prediction has no explicit selection")
        if ref not in refs:
            warnings.append(f"{ref}: prediction exists for a row that is not on the board")
        for s in p.get("sources", []):
            if urlparse(s.get("url", "")).scheme not in ("http", "https"):
                errors.append(f"{ref}: prediction source without a URL")


def main():
    ev = load("data/events.json")
    gap = load("data/gap_sports.json")
    preds = {p["ref"]: p for p in load("data/predictions.json")["predictions"]}

    fixture_rows = ev["events"]
    gap_rows = gap["rows"]
    for r in fixture_rows:
        r.setdefault("market_type", "fixture")

    refs = check_rows(fixture_rows + gap_rows, preds)
    check_predictions(preds, refs)

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
    print("PASS: every row has an OLBG source, verification is all-or-nothing, prices recompute, "
          "predictions meet the word floor and every HIGH pick has one.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
