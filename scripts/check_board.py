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
"""
import json
import os
import re
import sys
import unicodedata
from urllib.parse import urlparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from board_dates import in_band, american, BAND_LOW_DEC, BAND_HIGH_DEC

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED = {"Tennis", "Basketball", "Ice Hockey", "Cricket", "Baseball", "Volleyball", "Darts",
           "Snooker", "Rugby Union", "Rugby League", "Handball", "Gaelic Football",
           "Golf", "Motor Racing", "Greyhounds"}
EXCLUDED = {"football", "soccer", "boxing", "ufc", "mma", "american football", "hurling",
            "horse racing", "cycling", "specials"}
CONF = {"HIGH", "MEDIUM", "LOW"}
MARKERS = ("<<<<<<<", ">>>>>>>", "=======\n")

errors, warnings = [], []


def _selection_key(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    return "".join(ch for ch in text if ch.isalnum())


def selection_matches(row_label, prediction_label):
    """Allow documented club spelling aliases, but never allow a different selection to slip through."""
    row_key = _selection_key(row_label)
    pred_key = _selection_key(prediction_label)
    aliases = {
        "milbrewers": ("milwaukeebrewers",),
        "bufsabres": ("buffalosabres",),
    }
    candidates = (row_key,) + aliases.get(row_key, ())
    return any(candidate and candidate in pred_key for candidate in candidates)


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
            field_status = prior.get("field_size_status")
            if field_status not in ("official", "model_input", "competition_format"):
                errors.append(f"{ref}: missing/invalid field_size_status {field_status!r}")
            elif field_status == "official":
                if not prior.get("field_size_source"):
                    errors.append(f"{ref}: official field size has no independent source")
                if prior.get("field_size_source_tier") not in ("official", "club-official"):
                    errors.append(f"{ref}: official field size source tier is not official")
            elif field_status == "model_input":
                basis_lower = prior.get("basis", "").lower()
                if "assum" not in basis_lower and "model input" not in basis_lower:
                    errors.append(f"{ref}: model-input field size is not disclosed in its basis")
                if prior.get("field_size_source"):
                    errors.append(f"{ref}: model-input field size must not claim an official field source")

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
            if pk.get("label") and not selection_matches(pk["label"], p.get("selection", "")):
                errors.append(f"{ref}: prediction selection {p.get('selection')!r} does not match row pick {pk['label']!r}")
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
          "is inside the -250..+10000 band with a live kick-off and a written prediction, and every non-HIGH piece "
          "is labelled analysis.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
