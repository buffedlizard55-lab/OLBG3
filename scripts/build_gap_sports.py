#!/usr/bin/env python3
"""build_gap_sports.py - originate our own prices for OLBG's outright/race markets.

Input : data/raw/gap_sports_capture_20261021.json  (verbatim OLBG listing capture + our disclosed assumptions)
Output: data/gap_sports.json                       (rows in the same schema as data/events.json)

Why this exists
---------------
The main board (data/events.json) only carries two-sided fixtures. OLBG also publishes tournament and
race winner markets for Golf, Motor Racing, Greyhounds, Rugby League and the Gaelic football
championship. They are in scope (none of them is in the exclusion list) and they were previously
disclosed as an uncaptured gap. This script prices them so the board is complete, without pretending a
one-selection market has a second side or a handicap.

The price is ours, not a bookmaker's. It is built only from inputs that are on the OLBG page plus one
disclosed assumption (the size of the field), exactly as the two-sided model does:

    prior        Beta(a, b) with mean 1/N and strength k
                 a = k / N,  b = k - k / N
    probability  p = (wins + a) / (total + k)        # i.e. the tip share shrunk toward 1/N
    offered      decimal = (1 - 0.05) / p            # 5% overround, same as the two-sided model

N is the field size and k is the prior strength; both are listed per basis below and copied into the
output so every number can be reproduced and challenged. Nothing here is a verified fact.
"""
import json
import os
from urllib.parse import urlparse

import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from board_dates import resolve_start, resolve_kickoff_utc, started, american, in_band, AS_OF

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Source tiers, exactly as scripts/model.py applies them: only a competition's own site (or a club's own
# site) counts as verified; a third party is labelled corroborated and listed on Flagged for Review.
_TIERS = json.load(open(os.path.join(ROOT, "data/official.json")))["source_tiers"]


def _bare(host):
    host = (host or "").lower().split(":")[0].strip()
    return host[4:] if host.startswith("www.") else host


def source_tier(url):
    host = _bare(urlparse(url or "").netloc)
    if not host:
        return "unclassified"
    for tier in ("official", "club-official", "third-party"):
        for known in _TIERS[tier]:
            k = _bare(known)
            if host == k or host.endswith("." + k):
                return tier
    return "unclassified"


def graded_verification(v):
    url = v.get("official_url", "")
    tier = source_tier(url)
    out = dict(v, source_tier=tier)
    if out.get("status") == "verified" and tier not in ("official", "club-official"):
        out["status"] = "corroborated"
        out["note"] = (out.get("note", "") + " | SOURCE TIER: third-party link, published as corroborated rather "
                       "than verified.").strip()
    return out

SRC = os.path.join(ROOT, "data/raw/gap_sports_capture_20261021.json")
OUT = os.path.join(ROOT, "data/gap_sports.json")

OVERROUND = 0.05

# k = prior strength (how many "virtual tips" of the field-size prior we add).
# Chosen so that a single tip on a 156-player golf field cannot imply a 60% chance.
STRENGTH = {
    "golf_field_156": 24,
    "f1_grid_22": 12,
    "greyhound_six_dog": 6,
    "state_of_origin_two_side": 4,
    "super_league_twelve": 6,
    "nrl_seventeen": 6,
    "all_ireland_32": 10,
}


def price(p: float) -> float:
    """Decimal odds we would offer, with a 5% overround, rounded to 2dp."""
    return round((1 - OVERROUND) / p, 2)


def grade(fixture_verified: bool, official_form: bool, prob: float, field: int, total_tips: int) -> tuple[str, int, dict]:
    """Same 0-6 rubric the two-sided board uses (see method page), adapted to field priors."""
    factors = {
        "fixture_verified": 2 if fixture_verified else 0,
        "official_form": 2 if official_form else 0,
        "model_edge": 0,
    }
    prior_p = 1.0 / max(field, 2)
    if prob > 0.70 or (total_tips >= 20 and prob >= 5.0 * prior_p):
        factors["model_edge"] = 2
    elif prob >= 0.55 or (total_tips >= 10 and prob >= 3.0 * prior_p):
        factors["model_edge"] = 1
    score = sum(factors.values())
    label = "HIGH" if score >= 6 else ("MEDIUM" if score >= 3 else "LOW")
    return label, score, factors


def main() -> None:
    cap = json.load(open(SRC))
    basis_table = cap["field_size_assumptions"]
    rows = []

    for e in cap["events"]:
        basis = e["field_basis"]
        if basis not in basis_table:
            raise SystemExit(f"unknown field basis {basis} on {e['ref']}")
        default_field = basis_table[basis]["field"]
        field = e.get("field_override", default_field)
        k = STRENGTH[basis]
        a, b = k / field, k - k / field

        # The published basis text must describe the field actually used for this row. When a
        # field_override replaces the generic assumption, say so and name the real number instead
        # of repeating "assumed 156-player field" next to field=120.
        field_basis = basis_table[basis]["basis"]
        if field != default_field:
            if e["verification"].get("status") == "verified":
                field_basis = (
                    f"Field size {field}, not the generic {default_field} assumption used when a field "
                    f"is not published: the official competition source recorded for this row states a "
                    f"{field}-strong field, so the prior mean is 1/{field}. See this row's official "
                    f"source for the field statement."
                )
            else:
                field_basis = (
                    f"Field size {field}, not the generic {default_field} assumption: this row is a "
                    f"derived market rather than a published field, so {field} is an explicit model "
                    f"input recorded here and not a verified competition fact."
                )

        won, total = e["tips_won"], e["tips_total"]
        flags = []
        if won is None or total is None:
            prob, odds = None, None
            flags.append("no_tip_count_published")
        else:
            raw_prob = (won + a) / (total + k)
            prob = round(raw_prob, 4)
            odds = price(raw_prob)
            if total < 5:
                flags.append("small_sample_lt5_tips")
        if e["market_type"] == "outright":
            flags.append("outright_no_opposing_side")
        flags.append("field_size_prior_assumed")
        if e["verification"]["status"] != "verified":
            flags.append("official_source_not_retrieved")

        gv = graded_verification(e["verification"])
        is_ver = gv["status"] == "verified"
        conf, score, factors = grade(
            is_ver,
            bool(e.get("official_form_verified")),
            prob or 0.0,
            field,
            total or 0,
        )
        start_iso, start_basis = resolve_start(e["start"])
        kickoff_utc, clock_basis = resolve_kickoff_utc(e["start"])
        clock_started = started(e["start"])
        kickoff_passed = bool(start_iso) and start_iso < AS_OF.isoformat()
        band_ok = in_band(odds)
        if conf == "HIGH" and (kickoff_passed or not band_ok):
            conf = "MEDIUM"

        rows.append({
            "ref": e["ref"],
            "sport": e["sport"],
            "sport_slug": e["sport_slug"],
            "competition": e["competition"],
            "home": e["event_name"],
            "away": "",
            "start": e["start"],
            "market_type": e["market_type"],
            "olbg_market": e["olbg_market"],
            "olbg_pick": e["olbg_pick"],
            "olbg_tips": (f"{won}/{total}" if won is not None else None),
            "olbg_pct": e["olbg_pct"],
            "olbg_event_url": e["olbg_event_url"],
            "olbg_event_id": e["olbg_event_id"],
            "olbg_listing_url": cap["listing_pages"][e["sport"]],
            "venue": e["venue"],
            "verification": graded_verification(e["verification"]),
            "model": {
                "basis": "outright-prior" if e["market_type"] == "outright" else "race-prior",
                "prices": ({"single": odds} if odds else {}),
                "probs": ({"single": prob} if prob else {}),
                "prior": {"field": field, "strength_k": k, "a": round(a, 4), "b": round(b, 4),
                          "basis": field_basis},
                "notes": [
                    "Probability = (wins + a) / (total + k): the OLBG tip share shrunk toward a 1/N field prior.",
                    "No handicap and no total: a one-selection market has no opposing side to handicap and no scoring baseline on the page.",
                ],
            },
            "pick": {
                "side": "single",
                "label": e["olbg_pick"],
                "prob": prob,
                "confidence": conf,
                "score": score,
                "factors": factors,
                "price": odds,
                "american": american(odds) if odds else None,
                "in_band": band_ok,
                "band": [-250, 10000],
                "start_iso": start_iso,
                "kickoff_utc": kickoff_utc, "clock_basis": clock_basis,
                "kickoff_started": clock_started,
                "start_basis": start_basis,
                "kickoff_passed": kickoff_passed,
                "evidence_grade": conf,
                "note": "",
            },
            "flags": flags,
            "row_notes": e["row_notes"],
            "captured_at": cap["captured_at"],
        })

    payload = {
        "generated_at": cap["captured_at"],
        "source_capture": os.path.relpath(SRC, ROOT),
        "listing_pages": cap["listing_pages"],
        "model": {
            "what": "Our own prices for OLBG outright and race-winner markets.",
            "inputs": "Only the OLBG tip split and the disclosed field-size assumption below.",
            "formula": "p = (wins + a) / (total + k), Beta(a,b) prior with mean 1/N; decimal odds = (1 - 0.05) / p",
            "overround": OVERROUND,
            "strength_k_by_basis": STRENGTH,
            "field_sizes": {k: v["field"] for k, v in basis_table.items()},
            "caveat": "Model output, not a bookmaker price and not a fact. Where the tip count is missing, no price is originated.",
        },
        "rows": rows,
    }
    with open(OUT, "w") as fh:
        json.dump(payload, fh, indent=1)
        fh.write("\n")
    print(f"gap rows written: {len(rows)} -> {os.path.relpath(OUT, ROOT)}")
    priced = sum(1 for r in rows if r["model"]["prices"])
    print(f"priced {priced}, unpriced {len(rows) - priced}")


if __name__ == "__main__":
    main()
