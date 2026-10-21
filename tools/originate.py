#!/usr/bin/env python3
"""Originate our own lines for every fixture in data/matches.json.

This is a model, and it is documented as such (see data/model.md). It does not copy
bookmaker prices: OLBG does not publish prices in the retrieved pages anyway. Inputs are
(a) the tip split OLBG publishes for the fixture, (b) a home-field adjustment, and
(c) sport-level dispersion/mean assumptions used to place handicap and total lines.

Output: data/lines.json
"""
from __future__ import annotations

import json
import math
from pathlib import Path
from statistics import NormalDist

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ND = NormalDist()

# sigma = assumed standard deviation of the winning margin in that sport's own unit;
# total = our baseline total line; home = home-field edge in logit units.
SPORT_PARAMS = {
    "Cricket":      {"unit": "runs",  "sigma": 25.0, "total": None,  "home": 0.05},
    "Tennis":       {"unit": "games", "sigma": 4.0,  "total": 22.5,  "home": 0.00},
    "Basketball":   {"unit": "points","sigma": 11.5, "total": None,  "home": 0.16},
    "Snooker":      {"unit": "frames","sigma": 2.3,  "total": 5.5,   "home": 0.00},
    "Darts":        {"unit": "legs",  "sigma": 3.0,  "total": 10.5,  "home": 0.00},
    "Rugby Union":  {"unit": "points","sigma": 13.5, "total": 48.5,  "home": 0.18},
    "Rugby League": {"unit": "points","sigma": 16.0, "total": 46.0,  "home": 0.18},
    "Ice Hockey":   {"unit": "goals", "sigma": 1.8,  "total": 5.5,   "home": 0.13},
    "Baseball":     {"unit": "runs",  "sigma": 2.0,  "total": 8.5,   "home": 0.10},
    "Volleyball":   {"unit": "sets",  "sigma": 1.25, "total": 4.5,   "home": 0.12},
    "Handball":     {"unit": "goals", "sigma": 7.5,  "total": 58.5,  "home": 0.12},
    "Golf":         {"unit": None,    "sigma": None, "total": None,  "home": 0.00},
    "Motor Racing": {"unit": None,    "sigma": None, "total": None,  "home": 0.00},
    "Greyhounds":   {"unit": None,    "sigma": None, "total": None,  "home": 0.00},
    "Gaelic Football": {"unit": "points", "sigma": None, "total": None, "home": 0.10},
}

PRIOR_STRENGTH = 4.0   # Beta(2,2) prior: shrinks small samples toward even money
MARGIN = 0.05          # 5% theoretical hold on our two-way price


def logit(p: float) -> float:
    p = min(max(p, 1e-6), 1 - 1e-6)
    return math.log(p / (1 - p))


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def price(p: float) -> float:
    """Our quoted decimal price for a side with model probability p."""
    return round(max(1.01, 1 / (p * (1 + MARGIN))), 2)


def round_half(x: float) -> float:
    return round(x * 2) / 2


def total_line(match: dict) -> tuple[float | None, str | None]:
    sport = match["sport"]
    if sport == "Cricket":
        name = match["event_name"].lower()
        if "odi" in name or "one day" in name:
            return 290.5, "limited-overs baseline (model assumption)"
        return 320.5, "T20 baseline (model assumption)"
    if sport == "Basketball":
        if (match.get("competition") or "").startswith("NBA"):
            return 228.5, "NBA baseline (model assumption)"
        return 165.5, "European club baseline (model assumption)"
    baseline = SPORT_PARAMS.get(sport, {}).get("total")
    if baseline is None:
        return None, None
    return baseline, "baseline anchored to published league averages / typical lines (model assumption)"


def main() -> None:
    matches = json.loads((DATA / "matches.json").read_text())
    predictions_path = DATA / "predictions.json"
    preds = json.loads(predictions_path.read_text()) if predictions_path.exists() else {"predictions": []}
    high_ids = {p["match_id"] for p in preds.get("predictions", [])}

    out = []
    for m in matches:
        sport = m["sport"]
        params = SPORT_PARAMS[sport]
        won, total = m.get("olbg_tips_won"), m.get("olbg_tips_total")
        consensus = m.get("olbg_consensus_selection")
        flags: list[str] = []

        p_raw = p_shrunk = p_model = None
        basis = "no_probability_originated"
        if m["market_family"] == "match_winner" and won is not None and total:
            p_raw = won / total
            p_shrunk = (won + PRIOR_STRENGTH / 2) / (total + PRIOR_STRENGTH)
            shift = 0.0
            if m["home"] and consensus == m["home"]:
                shift = params["home"]
            elif m["away"] and consensus == m["away"]:
                shift = -params["home"]
            p_model = sigmoid(logit(p_shrunk) + shift)
            basis = "tip split shrunk with Beta(2,2) prior, then home-field logit shift"
            if total < 5:
                flags.append("small_sample_lt5_tips")
            if shift:
                flags.append("home_field_adjustment_applied")
        elif m["market_family"] == "match_winner":
            flags.append("no_split_available")
        elif m["market_family"] == "other" and m["home"] and m["away"]:
            # The OLBG row for this fixture is not a winner market (total, handicap, set
            # betting ...), so we have no tip split for the moneyline. We originate a
            # line from the home edge alone and say so.
            side = None
            if consensus and m["away"] and m["away"] in consensus:
                side = "away"
            elif consensus and m["home"] and m["home"] in consensus:
                side = "home"
            else:
                side = "home"
            shift = params["home"] if side == "home" else -params["home"]
            p_model = sigmoid(shift)
            basis = "no winner-market split available; line originated from home-field edge only"
            flags += ["olbg_row_is_non_winner_market", "no_split_on_winner_market"]
        else:
            flags.append("outright_or_race_no_head_to_head_line")

        # pick + price
        pick = None
        p_pick = None
        other = None
        if m["market_family"] in ("match_winner", "other") and p_model is not None and m["home"] and m["away"]:
            if p_model >= 0.5:
                pick = consensus if consensus in (m["home"], m["away"]) else m["home"]
                p_pick = p_model
                other = m["away"] if pick == m["home"] else m["home"]
            else:
                pick = m["away"] if consensus == m["home"] else m["home"]
                p_pick = 1 - p_model
                other = m["home"] if pick == m["away"] else m["away"]
        elif consensus:
            pick = consensus
            flags.append("pick_carried_from_olbg_consensus_without_our_probability")

        # handicap line, only when we have our own probability
        hc = hc_side = None
        if p_model is not None and pick and params["sigma"]:
            fav_p = max(p_model, 1 - p_model)
            z = ND.inv_cdf(min(fav_p, 0.995))
            hc = -round_half(params["sigma"] * z)
            if hc == 0:
                hc = 0.0  # pick'em: no side gives a start
            hc_side = pick if p_pick >= 0.5 else other
        tl, tl_basis = total_line(m)
        if tl is None:
            flags.append("no_defensible_total_baseline_blank")

        # confidence
        if m["id"] in high_ids:
            conf = "high"
        elif (m["market_family"] == "match_winner" and total and total >= 5
              and p_model is not None and abs(p_model - 0.5) >= 0.08):
            conf = "medium"
        else:
            conf = "low"

        out.append({
            "match_id": m["id"],
            "sport": sport,
            "event_name": m["event_name"],
            "home": m["home"],
            "away": m["away"],
            "competition": m["competition"],
            "start": m.get("verified_start") or f"{m.get('date_iso')} (OLBG label: {m['olbg_date_label']} {m['olbg_time_label']})",
            "olbg_url": m["olbg_url"],
            "inputs": {
                "olbg_market": m["olbg_market"],
                "olbg_consensus_selection": consensus,
                "olbg_tips": m.get("olbg_tips"),
                "p_raw": None if p_raw is None else round(p_raw, 4),
                "p_shrunk": None if p_shrunk is None else round(p_shrunk, 4),
                "basis": basis,
            },
            "our_match_probability": None if p_model is None else round(p_model, 4),
            "our_pick": pick,
            "our_pick_probability": None if p_pick is None else round(p_pick, 4),
            "our_fair_odds": None if p_pick is None else round(1 / p_pick, 2),
            "our_price_pick": None if p_pick is None else price(p_pick),
            "our_price_other": None if other is None or p_pick is None else price(1 - p_pick),
            "our_handicap_line": hc,
            "our_handicap_side": hc_side,
            "our_handicap_unit": params["unit"] if hc is not None else None,
            "our_total_line": tl,
            "our_total_unit": params["unit"] if tl is not None else None,
            "our_total_basis": tl_basis,
            "confidence": conf,
            "flags": flags,
        })

    (DATA / "lines.json").write_text(json.dumps(out, indent=2) + "\n")
    from collections import Counter
    print("lines:", len(out), Counter(o["confidence"] for o in out))


if __name__ == "__main__":
    main()
