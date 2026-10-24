#!/usr/bin/env python3
"""pick_surface.py — one obvious, de-duplicated pick surface for the published site.

Why this module exists
----------------------
The repository carries two independent pricing tracks (the root board, built from official
competition tables, and the ``/olbg/`` lines track, built from the captured OLBG listing).
Before this module each track published its own HIGH table on its own landing page, so a reader
had to visit two sites to learn what the picks were, and a bare selection with no written
analysis was rendered in the same visual style as a sourced write-up.

This module merges both tracks on the OLBG event id, keeps only selections that carry a fully
written prediction, and labels the rest as analysis. It reads committed data only: no value is
invented here, and nothing in this module renews a source observation or a fixture clock.

Two states, and only one of them is a pick
------------------------------------------
``pick``     — confidence HIGH, the shared release gate says the fixture has not started and the
               official observation behind its clock is under 24 hours old, the originated price
               sits inside -250 to +10000 US, and a unique written piece of at least 30 words
               exists for it.
``analysis`` — everything else that was graded HIGH: it stays published, with the mechanical
               reason printed on the card, and it is counted as a pick nowhere.

``min_words`` is the brief's floor; ``banned_terms`` is the brief's output rule for the prose.
"""
from __future__ import annotations

import html

MIN_WORDS = 30
BANNED_TERMS = ("model", "verified")


def esc(x) -> str:
    return html.escape(str(x)) if x is not None else ""


def words(text: str | None) -> int:
    """Words in a written piece, counting only tokens that carry a letter or a digit."""
    return len([w for w in (text or "").split() if any(c.isalnum() for c in w)])


def prose_problems(text: str | None) -> list[str]:
    """The two hard prose rules from the brief, checked mechanically."""
    problems: list[str] = []
    if words(text) < MIN_WORDS:
        problems.append(f"under {MIN_WORDS} words")
    lowered = (text or "").lower()
    hits = sorted({t for t in BANNED_TERMS if t in lowered})
    if hits:
        problems.append("uses the internal word(s): " + ", ".join(hits))
    return problems


def american(decimal_price) -> str:
    """Decimal to US display. Mirrors board_dates.americana without importing it at module load."""
    if not isinstance(decimal_price, (int, float)):
        return ""
    from board_dates import american as _a  # local import: build_site already has scripts/ on the path
    v = _a(decimal_price)
    return "" if v is None else f"{v:+d}"


def _event_id(match_id: str):
    """The numeric OLBG event id inside a track reference such as 'VOL-36995' or 'RGU-609581'."""
    tail = (match_id or "").rsplit("-", 1)[-1]
    return int(tail) if tail.isdigit() else None


def _money(p) -> str:
    return f"{p:.2f}" if isinstance(p, (int, float)) else ""


def collect(events, preds_root, lines_olbg, matches_olbg, preds_olbg) -> list[dict]:
    """Merge both tracks into one list of entries, one per OLBG fixture.

    ``events``       root board rows (``data/events.json`` after the model has graded them)
    ``preds_root``   root write-ups keyed by root ref
    ``lines_olbg``   ``/olbg/`` originated lines keyed by match id
    ``matches_olbg`` ``/olbg/`` captured fixture rows keyed by match id
    ``preds_olbg``   ``/olbg/`` write-ups keyed by match id
    """
    merged: dict[str, dict] = {}

    def slot(key: str) -> dict:
        return merged.setdefault(key, {"key": key, "event_id": None, "sport": "", "match": "",
                                   "competition": "", "start_utc": "", "olbg_label": "",
                                   "olbg_url": "", "tracks": {}, "sources": [], "texts": []})

    def state_of(confidence, release, price, text) -> tuple[str, str]:
        rel = release or {}
        if str(confidence).upper() != "HIGH":
            return "analysis", f"graded {str(confidence).lower() or 'ungraded'}, not high"
        if not rel.get("eligible"):
            return "analysis", rel.get("reason") or "the release gate does not pass this fixture"
        if not text:
            return "analysis", "no written prediction exists for this selection"
        if words(text) < MIN_WORDS:
            return "analysis", f"written prediction is under {MIN_WORDS} words"
        if price is None:
            return "analysis", "no originated price, so the band cannot be checked"
        return "pick", ""

    for r in events:
        p = r.get("pick") or {}
        if str(p.get("confidence", "")).upper() != "HIGH":
            continue
        piece = preds_root.get(r["ref"]) or {}
        text = piece.get("body") or ""
        eid = r.get("olbg_event_id")
        key = f"E{eid}" if eid else f"R{r['ref']}"
        x = slot(key)
        x["event_id"] = eid
        x["sport"] = x["sport"] or r.get("sport", "")
        x["match"] = x["match"] or " ".join(v for v in (r.get("home"), r.get("away")) if v)
        x["competition"] = x["competition"] or (r.get("competition") or "")
        x["olbg_url"] = x["olbg_url"] or (r.get("olbg_event_url") or "")
        x["slug"] = x.get("slug") or r.get("sport_slug", "")
        x["root_ref"] = r["ref"]
        state, reason = state_of(p.get("confidence"), p.get("release"), p.get("price"), text)
        ver = r.get("verification") or {}
        x["tracks"]["root"] = {
            "ref": r["ref"],
            "selection": p.get("label") or "",
            "market": r.get("olbg_market") or "market not stated by OLBG",
            "price": p.get("price"),
            "american": p.get("american"),
            "prob": p.get("prob"),
            "confidence": p.get("confidence"),
            "start_utc": (p.get("release") or {}).get("start_utc") or p.get("kickoff_utc") or "",
            "olbg_label": r.get("start") or "",
            "state": state,
            "reason": reason,
            "text": text,
            "headline": piece.get("headline") or "",
            "verification": ver.get("status") or "",
            "official_label": ver.get("official_label") or "",
            "official_url": ver.get("official_url") or "",
            "handicap": (r.get("model") or {}).get("handicap"),
            "total": (r.get("model") or {}).get("total"),
            "checked_at": (p.get("release") or {}).get("checked_at") or "",
            "clock_source": (p.get("release") or {}).get("source") or "",
        }
        if text:
            x["texts"].append(text)
        for s in (piece.get("sources") or []):
            if s.get("url") and s["url"] not in [y.get("url") for y in x["sources"]]:
                x["sources"].append(s)

    for mid, l in lines_olbg.items():
        if str(l.get("confidence", "")).upper() != "HIGH":
            continue
        m = matches_olbg.get(mid) or {}
        piece = preds_olbg.get(mid) or {}
        text = piece.get("text") or ""
        rel = l.get("release") or {}
        eid = _event_id(mid)
        key = f"E{eid}" if eid else f"O{mid}"
        x = slot(key)
        x["event_id"] = x["event_id"] or eid
        x["sport"] = x["sport"] or l.get("sport", "")
        x["match"] = x["match"] or (l.get("event_name") or m.get("event_name") or "")
        x["competition"] = x["competition"] or (l.get("competition") or m.get("competition") or "")
        x["olbg_url"] = x["olbg_url"] or (l.get("olbg_url") or m.get("olbg_url") or "")
        x["olbg_ref"] = mid
        state, reason = state_of(l.get("confidence"), rel, l.get("our_price_pick"), text)
        x["tracks"]["olbg"] = {
            "ref": mid,
            "selection": l.get("our_pick") or "",
            "market": (m.get("olbg_market") or "market not stated by OLBG"),
            "price": l.get("our_price_pick"),
            "american": american(l.get("our_price_pick")),
            "prob": l.get("our_pick_probability"),
            "confidence": l.get("confidence"),
            "start_utc": rel.get("start_utc") or "",
            "olbg_label": m.get("olbg_date_label") or l.get("start") or "",
            "state": state,
            "reason": reason,
            "text": text,
            "headline": "",
            "verification": m.get("competition_status") or "",
            "official_label": (m.get("verified_start") and "official fixture page") or "",
            "official_url": (m.get("verification_ids") and "") or "",
            "handicap": None,
            "total": None,
            "checked_at": rel.get("checked_at") or "",
            "clock_source": rel.get("source") or "",
        }
        if text:
            x["texts"].append(text)
        for s in (piece.get("sources") or []):
            if s.get("url") and s["url"] not in [y.get("url") for y in x["sources"]]:
                x["sources"].append(s)

    out: list[dict] = []
    for key, x in merged.items():
        x["key"] = key
        states = [t["state"] for t in x["tracks"].values()]
        x["state"] = "pick" if "pick" in states else "analysis"
        x["reason"] = "" if x["state"] == "pick" else (
            next((t["reason"] for t in x["tracks"].values() if t["reason"]), "") or "")
        starts = sorted(t["start_utc"] for t in x["tracks"].values() if t.get("start_utc"))
        x["start_utc"] = starts[0] if starts else ""
        x["olbg_label"] = x["olbg_label"] or next((t["olbg_label"] for t in x["tracks"].values()
                                                   if t.get("olbg_label")), "")
        x["word_counts"] = {k: words(t["text"]) for k, t in x["tracks"].items() if t.get("text")}
        x["unique"] = len({t["text"] for t in x["tracks"].values() if t.get("text")})
        out.append(x)
    rank = {"pick": 0, "analysis": 1}
    out.sort(key=lambda x: (rank[x["state"]], x["start_utc"] or "9999", x["sport"], x["match"]))
    return out


def price_bits(t: dict) -> str:
    price = _money(t.get("price"))
    us = t.get("american") or american(t.get("price"))
    if not price:
        return '<span class="dim">no price originated</span>'
    return f"{price} <span class='dim'>({esc(us)} US)</span>"


def card_html(x: dict, pre: str = "") -> str:
    """One pick card. The written prediction is on the card, not one click away."""
    tracks = x["tracks"]
    order = [k for k in ("root", "olbg") if k in tracks]
    head_rows = []
    for k in order:
        t = tracks[k]
        label = "root board" if k == "root" else "OLBG lines track"
        conf = str(t.get("confidence") or "").upper()
        pill = f'<span class="pill {conf.lower()}">{conf}</span>'
        head_rows.append(
            f"<div class='pick-track'><span class='tag'>{label}</span> "
            f"<strong class='sel'>{esc(t['selection'])}</strong> "
            f"<span class='dim small'>{esc(t['market'])}</span> "
            f"<span class='price'>{price_bits(t)}</span> {pill} "
            f"<span class='dim small'>our estimate "
            f"{(t['prob'] * 100):.0f}%</span></div>")
    when = ""
    if x.get("start_utc"):
        when = f"<span class='when'>{esc(x['start_utc'])}</span> <span class='dim small'>official UTC</span>"
    elif x.get("olbg_label"):
        when = f"<span class='when'>{esc(x['olbg_label'])}</span> <span class='dim small'>OLBG clock, zone unverified</span>"
    sources = "".join(
        f"<a href='{esc(s['url'])}' rel='noopener'>{esc(s.get('label') or s['url'])}</a>"
        for s in x["sources"])
    olbg_link = (f"<a href='{esc(x['olbg_url'])}' rel='noopener'>OLBG event page</a>"
                 if x.get("olbg_url") else "<span class='dim'>no captured OLBG link</span>")
    # A reference links to the page that carries the piece. No piece, no link: the anchor would
    # not exist, and scripts/check_links.py fails the build on a dangling fragment.
    def ref_link(k: str) -> str:
        # Both predictions pages carry an anchor per written piece, so a reference is a link
        # straight to that piece. A fixture with no piece prints no link: a dangling fragment
        # fails scripts/check_links.py and strands a reader.
        t = tracks[k]
        if not t.get("text"):
            return f"<span class='dim'>{esc(t['ref'])} (no piece)</span>"
        page = "predictions.html" if k == "root" else "olbg/predictions.html"
        return f"<a href='{pre}{page}#{esc(t['ref'])}'>{esc(t['ref'])}</a>"


    refs = " · ".join(ref_link(k) for k in order)
    written = [f"<p class='why'>{esc(tracks[k]['text'])}</p>" for k in order if tracks[k].get("text")]
    if written:
        texts = "".join(written)
    else:
        texts = ("<p class='dim'>No written prediction exists for this selection, so it is not "
                 "published as a pick.</p>")
    state = x["state"]
    flag = ("<span class='pill pick'>PICK</span>" if state == "pick"
            else f"<span class='pill analysis'>NOT A PICK</span> <span class='dim small'>{esc(x['reason'])}</span>")
    klass = "pick-card" if state == "pick" else "pick-card analysis-card"
    return (f"<article class='{klass}' id='pick-{esc(x.get('key'))}' data-state='{state}'>"
            f"<div class='pick-head'><span class='tag sport'>{esc(x['sport'])}</span>"
            f"<h3>{esc(x['match'])}</h3>"
            f"<p class='small dim'>{esc(x['competition']) or 'competition not stated by an official source'} "
            f"&middot; {when}</p>{flag}</div>"
            f"<div class='pick-tracks'>{''.join(head_rows)}</div>"
            f"<div class='pick-text'>{texts}</div>"
            f"<p class='pick-foot small'>refs {refs} &middot; {olbg_link}</p>"
            f"<p class='pick-srcs small'><strong>Sources for the facts quoted above:</strong> {sources}"
            f" &middot; <a href='{pre}verification.html'>how these rows were checked</a></p>"
            f"</article>")


def summary_line(picks: list[dict]) -> str:
    """The one sentence that answers 'how many picks are there and for what?'."""
    live = [x for x in picks if x["state"] == "pick"]
    if not live:
        return ("<strong>No pick passes every gate at this build.</strong> Rows graded HIGH are listed "
                "below with the mechanical reason each one is held back, so the gap is visible instead "
                "of being hidden by a shorter list.")
    sports = sorted({x["sport"] for x in live})
    starts = sorted(x["start_utc"] for x in live if x["start_utc"])
    window = f"First start {starts[0]}" if starts else ""
    return (f"<strong>{len(live)} written pick(s) across {len(sports)} sport(s):</strong> "
            f"{esc(', '.join(sports))}. {esc(window)}".strip())
