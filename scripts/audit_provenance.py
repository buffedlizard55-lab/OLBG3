#!/usr/bin/env python3
"""Independent capture-to-publication provenance audit for the OLBG lines track.

This is deliberately not a sporting-fact verifier.  It answers a narrower, reproducible
question: do the published rows preserve the committed OLBG observations, declared source
precedence, live overrides, verification-register references, line arithmetic and written
selection metadata?  Official-page freshness and factual truth require a separate read.

The report is deterministic for a fixed input tree.  It includes input SHA-256 hashes and
uses the committed publication clock rather than inventing an observation timestamp.
Errors are internal inconsistencies.  Warnings are review items (including conflicts
between source observations).  Informational entries describe ordinary market movement.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import itertools
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

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
WIN_MARKETS = {"Win Match", "Win Match 2-way", "Money Line", "To Win"}
OUTRIGHT_MARKETS = {
    "Win Tournament", "Grand Final Winner", "Daily Races", "Outright Winner",
    "Fastest Qualifier", "Win Race",
}
TIPS_RE = re.compile(r"^\s*(\d+)\s*/\s*(\d+)")
SUFFIX_RE = re.compile(
    r"\s+(One Day Match|1st T20 Match|2nd T20 Match|3rd T20 Match|T20|1st ODI|2nd ODI|3rd ODI)$"
)
BANNED_PREDICTION_TERMS = re.compile(r"\b(?:model|verified)\b", re.I)
MARKET_WORDS = re.compile(
    r"money\s*line|match\s+winner|\bwin\b|\bto\s+win\b|handicap|\bover\b|\bunder\b|\brace\b",
    re.I,
)


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalise_space(value: str | None) -> str:
    return " ".join((value or "").split())


def normalise_name(value: str | None) -> str:
    # Unicode letters are preserved (Brynäs/Brynäs); punctuation only separates tokens.
    return " ".join(re.findall(r"[^\W\d_]+|\d+", (value or "").casefold()))


def load_name_aliases(root: Path) -> dict[str, str]:
    """Read the repository's declared name-normalisation tables without executing the builder."""
    path = root / "scripts" / "model.py"
    if not path.exists():
        return {}
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    tables: dict[str, dict] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in ("ALIASES", "PICK_NAME_ALIASES"):
                try:
                    tables[target.id] = ast.literal_eval(node.value)
                except (ValueError, TypeError):
                    tables[target.id] = {}
    aliases = dict(tables.get("ALIASES", {}))
    # PICK_NAME_ALIASES runs full name -> OLBG abbreviation; compare in the other direction too.
    for full_name, abbreviation in tables.get("PICK_NAME_ALIASES", {}).items():
        aliases.setdefault(abbreviation, full_name)
    return aliases


def selection_names_pick(pick: str, selection: str, aliases: dict[str, str]) -> bool:
    """Conservative textual identity check, including declared aliases and common club abbreviation.

    A nickname alone is not enough: an abbreviated prefix must expand by initials or by its
    letters (PIT -> Pittsburgh, MIL -> Milwaukee) and every remaining nickname token must
    match.  Thus 'PIT Penguins' cannot silently match 'Nashville Penguins'.
    """
    pick_norm = normalise_name(pick)
    selection_norm = normalise_name(selection)
    if pick_norm and pick_norm in selection_norm:
        return True
    alias = aliases.get(pick)
    if alias and normalise_name(alias) in selection_norm:
        return True

    candidate = re.split(
        r"\s+(?:to\s+win\b|match\s+winner\b|money\s*line\b|win\s+match\b)",
        selection.strip(), maxsplit=1, flags=re.I,
    )[0]
    pick_raw_tokens = pick.strip().split()
    pick_tokens = normalise_name(pick).split()
    candidate_tokens = normalise_name(candidate).split()
    if len(pick_raw_tokens) < 2 or len(pick_tokens) < 2:
        return False
    abbreviation = pick_raw_tokens[0].strip(".")
    nickname = pick_tokens[1:]
    if not abbreviation.isupper() or not 2 <= len(abbreviation) <= 3:
        return False
    if len(candidate_tokens) <= len(nickname) or candidate_tokens[-len(nickname):] != nickname:
        return False
    prefix = candidate_tokens[:-len(nickname)]
    abbr = abbreviation.casefold()
    initials = "".join(token[0] for token in prefix if token)
    return bool(prefix) and (initials == abbr or prefix[0].startswith(abbr))


def parse_tips(label: str | None) -> tuple[int | None, int | None]:
    match = TIPS_RE.match(label or "")
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def numeric_or_none(value: str | None) -> float | None:
    """Parse a captured decimal without turning an unreadable value into a crash or a guess."""
    if value is None or not str(value).strip():
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def split_teams(event_name: str) -> tuple[str | None, str | None]:
    if " @ " in event_name:
        away, home = event_name.split(" @ ", 1)
        return home.strip(), away.strip()
    for separator in (" vs ", " v "):
        if separator in event_name:
            home, away = event_name.split(separator, 1)
            return home.strip(), away.strip()
    return None, None


def resolve_date(label: str, run_day: date) -> str | None:
    label = label.strip()
    if label == "Today":
        return run_day.isoformat()
    if label == "Tomorrow":
        return (run_day + timedelta(days=1)).isoformat()
    match = re.match(r"^(\d{1,2}) (\w{3})$", label)
    if match:
        day = int(match.group(1))
        month = datetime.strptime(match.group(2), "%b").month
        year = run_day.year if month >= run_day.month else run_day.year + 1
        return date(year, month, day).isoformat()
    match = re.match(r"^(\d{1,2}) (\w{3}) (\d{4})$", label)
    if match:
        return datetime.strptime(label, "%d %b %Y").date().isoformat()
    return None


def event_url(prefix: str, slug: str, sport_id: int, event_id: str) -> str:
    prefix = prefix.strip("/")
    if prefix.endswith("/" + slug) or prefix == slug:
        return f"https://www.olbg.com/betting-tips/{prefix}/{sport_id}?event_id={event_id}"
    return f"https://www.olbg.com/betting-tips/{prefix}/{slug}/{sport_id}?event_id={event_id}"


def market_family(market: str) -> str:
    if market in WIN_MARKETS:
        return "match_winner"
    if market in OUTRIGHT_MARKETS:
        return "outright"
    return "other"


def competition_status(verification: dict) -> str:
    if not verification.get("competition"):
        return "not_stated_by_source"
    status = verification.get("status") or "unverified"
    if status in ("verified", "verified_market_row"):
        return "verified"
    if status == "verified_secondary_only":
        return "corroborated_only"
    return "partial"


def make_issue(severity: str, code: str, message: str, **context) -> dict:
    # Context values must remain JSON serialisable and source-led; no inferred replacements.
    return {"severity": severity, "code": code, "message": message, **context}


def source_reference(row: dict) -> dict:
    return {
        "capture": row.get("source_file"),
        "line": row.get("source_line"),
        "fetched_at": row.get("fetched_at"),
        "listing_url": row.get("listing_url") or None,
        "event_url": row.get("event_url"),
    }


def capture_sources(meta: dict) -> list[dict]:
    """Return sources in the same explicit precedence order declared by meta.json."""
    started = meta["run_started_utc"]
    primary_completed = meta.get("harvest_completed_utc", "")
    sources = [{
        "role": "primary",
        "file": meta.get("harvest_file", "raw/olbg-harvest-20261021.tsv"),
        "format": meta.get("harvest_format", "v1"),
        "fetched_at": primary_completed or "2026-10-21T05:20:00Z",
        "day": meta.get("olbg_locale_date") or started[:10],
        "carry_note": None,
    }]
    previous = meta.get("previous_harvest") or {}
    if previous.get("file"):
        completed = previous.get("harvest_completed_utc", "")
        sources.append({
            "role": "previous",
            "file": previous["file"],
            "format": previous.get("format", "v1"),
            "fetched_at": completed,
            "day": previous.get("olbg_locale_date") or (completed or started)[:10],
            "carry_note": (
                f"carried from the {completed[:16]} harvest: fixture started or rotated off "
                f"OLBG listing prior to {primary_completed[:16]}Z"
            ),
        })
    for index, extra in enumerate(meta.get("supplementary_harvests", []), start=1):
        if not extra.get("file"):
            continue
        completed = extra.get("harvest_completed_utc", "")
        sources.append({
            "role": f"supplementary_{index}",
            "file": extra["file"],
            "format": extra.get("format", "v2"),
            "fetched_at": completed,
            "day": extra.get("olbg_locale_date") or (completed or started)[:10],
            "carry_note": (
                f"supplementary evening capture at {completed}: event not present in earlier captures"
            ),
        })
    for extra in meta.get("previous_harvests_extra", []):
        if not extra.get("file"):
            continue
        completed = extra.get("harvest_completed_utc", "")
        sources.append({
            "role": "previous_extra",
            "file": extra["file"],
            "format": extra.get("format", "v1"),
            "fetched_at": completed,
            "day": extra.get("olbg_locale_date") or (completed or started)[:10],
            "carry_note": (
                f"carried from the {completed[:16]} harvest: fixture started or rotated off "
                f"OLBG listing prior to {primary_completed[:16]}Z"
            ),
        })
    return sources


def parse_capture_line(line: str, source: dict, line_number: int) -> dict:
    parts = line.split("|")
    parts += [""] * max(0, 18 - len(parts))
    league_label = ""
    start_utc = odds_decimal = odds_american = odds_fractional = ""
    tip_share = event_title = listing_url = ""
    percentage = ""
    if source["format"] == "v3":
        (sport, league_label, prefix, slug, event_id, date_label, time_label,
         market, consensus, tips, note, start_utc, odds_decimal, odds_american,
         odds_fractional, tip_share, event_title, listing_url) = parts[:18]
    elif source["format"] == "v2":
        (sport, league_label, prefix, slug, event_id, date_label, time_label,
         market, consensus, tips, note) = parts[:11]
    else:
        (sport, prefix, slug, event_id, date_label, time_label,
         market, consensus, tips, percentage, note) = parts[:11]
    sport = sport.replace("_", " ").strip()
    sport_id = SPORT_IDS.get(sport)
    row = {
        "sport": sport,
        "sport_id": sport_id,
        "league_label": league_label,
        "prefix": prefix,
        "slug": slug,
        "event_id": event_id,
        "date_label": date_label,
        "time_label": time_label,
        "market": market,
        "consensus": consensus,
        "tips": tips,
        "note": note,
        "start_utc": start_utc,
        "odds_decimal": odds_decimal,
        "odds_american": odds_american,
        "odds_fractional": odds_fractional,
        "tip_share": tip_share or percentage,
        "event_title": event_title,
        "listing_url": listing_url,
        "source_file": source["file"],
        "source_role": source["role"],
        "source_line": line_number,
        "source_day": source["day"],
        "fetched_at": source["fetched_at"],
        "carry_note": source["carry_note"],
        "format": source["format"],
    }
    row["event_url"] = event_url(prefix, slug, sport_id, event_id) if sport_id else None
    return row


def read_captures(data_dir: Path, meta: dict) -> tuple[list[dict], list[dict], list[dict]]:
    observations: list[dict] = []
    issues: list[dict] = []
    sources = capture_sources(meta)
    for source in sources:
        path = data_dir / source["file"]
        if not path.exists():
            issues.append(make_issue(
                "error", "capture_missing", f"Declared capture is missing: {source['file']}",
                capture=source["file"],
            ))
            continue
        per_capture_ids: dict[str, list[int]] = defaultdict(list)
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            if not line.strip() or line.startswith("#"):
                continue
            row = parse_capture_line(line, source, line_number)
            observations.append(row)
            if row["event_id"]:
                per_capture_ids[row["event_id"]].append(line_number)
            if not row["event_id"].isdigit():
                issues.append(make_issue(
                    "error", "capture_event_id_invalid", "Capture row has no numeric OLBG event id",
                    **source_reference(row),
                ))
            if row["sport_id"] is None:
                issues.append(make_issue(
                    "error", "capture_sport_out_of_scope",
                    f"Capture sport is not one of the 15 covered sports: {row['sport']!r}",
                    **source_reference(row),
                ))
            for field in ("prefix", "slug"):
                if not row[field]:
                    issues.append(make_issue(
                        "error", "capture_url_part_missing", f"Capture row has a blank {field}",
                        field=field, **source_reference(row),
                    ))
            won, total = parse_tips(row["tips"])
            if row["tips"] and won is None:
                issues.append(make_issue(
                    "warning", "capture_tip_label_unparsed",
                    f"Tip label does not start with N/M: {row['tips']!r}",
                    **source_reference(row),
                ))
            if won is not None and total is not None and won > total:
                issues.append(make_issue(
                    "warning", "capture_tip_count_impossible",
                    f"Winning tip count exceeds total: {row['tips']!r}",
                    **source_reference(row),
                ))
            if row["format"] == "v3" and row["tip_share"] and total:
                try:
                    share = int(row["tip_share"])
                    calculated = round(100 * won / total)
                    if abs(share - calculated) > 1:
                        issues.append(make_issue(
                            "warning", "capture_tip_share_mismatch",
                            f"Tip share {share}% does not match {row['tips']} (about {calculated}%)",
                            expected=calculated, actual=share, **source_reference(row),
                        ))
                except ValueError:
                    issues.append(make_issue(
                        "warning", "capture_tip_share_invalid",
                        f"Tip share is not an integer: {row['tip_share']!r}",
                        **source_reference(row),
                    ))
            if row["start_utc"]:
                try:
                    datetime.fromisoformat(row["start_utc"].replace("Z", "+00:00"))
                except ValueError:
                    issues.append(make_issue(
                        "warning", "capture_start_invalid",
                        f"OLBG startDate is not ISO-8601: {row['start_utc']!r}",
                        **source_reference(row),
                    ))
            if row["odds_decimal"]:
                decimal_value = numeric_or_none(row["odds_decimal"])
                if decimal_value is None or decimal_value <= 1:
                    issues.append(make_issue(
                        "warning", "capture_decimal_price_invalid",
                        f"OLBG decimal price must be numeric and exceed 1 when present: {row['odds_decimal']!r}",
                        **source_reference(row),
                    ))
        for event_id, line_numbers in per_capture_ids.items():
            if len(line_numbers) > 1:
                issues.append(make_issue(
                    "warning", "same_capture_event_repeated",
                    f"Event {event_id} occurs {len(line_numbers)} times in one capture; review market preservation",
                    event_id=event_id, capture=source["file"], lines=line_numbers,
                ))
    return observations, issues, sources


def expected_match(row: dict, verification: dict, override: dict | None) -> dict:
    override = override or {}
    slug_name = row["slug"].replace("_", " ")
    source_home, source_away = split_teams(slug_name)
    if source_away:
        source_away = SUFFIX_RE.sub("", source_away)
    display = verification.get("fixture_name") or row["event_title"] or slug_name
    won, total = parse_tips(override.get("olbg_tips") or row["tips"])
    percentage = override.get("olbg_confidence_pct")
    if percentage is None:
        percentage = int(row["tip_share"]) if row["tip_share"].strip().isdigit() else None
    note = override.get("row_notes")
    if note is None:
        note = row["note"]
        if row["carry_note"]:
            note = (note + "; " if note else "") + row["carry_note"]
    date_iso = ((row["start_utc"] or "")[:10] or None) or resolve_date(
        row["date_label"], date.fromisoformat(row["source_day"])
    )
    expected = {
        "id": f"{ID_PREFIX.get(row['sport'], 'UNK')}-{row['event_id']}",
        "sport": row["sport"],
        "olbg_sport_id": row["sport_id"],
        "competition": verification.get("competition") or None,
        "competition_status": competition_status(verification),
        "venue": verification.get("venue") or None,
        "verified_start": verification.get("start_local") or None,
        "event_name": display,
        "home": verification.get("home") or source_home,
        "away": verification.get("away") or source_away,
        "olbg_date_label": row["date_label"],
        "olbg_time_label": row["time_label"],
        "date_iso": date_iso,
        "olbg_start_utc": row["start_utc"] or None,
        "olbg_start_basis": 'OLBG <time itemprop="startDate"> attribute' if row["start_utc"] else None,
        "olbg_odds_decimal": numeric_or_none(row["odds_decimal"]),
        "olbg_odds_american": row["odds_american"] or None,
        "olbg_market": override.get("olbg_market") or row["market"] or None,
        "market_family": market_family(override.get("olbg_market") or row["market"]),
        "olbg_consensus_selection": override.get("olbg_consensus_selection") or row["consensus"] or None,
        "olbg_tips": override.get("olbg_tips") or row["tips"] or None,
        "olbg_tips_won": won,
        "olbg_tips_total": total,
        "olbg_confidence_pct": percentage,
        "olbg_url": row["event_url"],
        "olbg_league_label": row["league_label"] or None,
        "verification_status": verification.get("status") or "unverified",
        "verification_note": verification.get("note") or None,
        "official_start_utc": verification.get("start_utc") or None,
        "fetched_at": row["fetched_at"],
        "verification_ids": verification.get("sources", []),
        "ambiguous_exclusion": row["sport"] == "Gaelic Football",
        "row_notes": note or None,
    }
    if row["odds_decimal"]:
        expected["olbg_odds_displayed_note"] = (
            "Price OLBG printed for this selection at capture time; not our line "
            "and not a bookmaker sheet read by this project."
        )
    else:
        expected["olbg_odds_displayed_note"] = None
    return expected


def decimal_to_american(price: float) -> str:
    if price >= 2:
        return f"+{round((price - 1) * 100)}"
    return f"-{round(100 / (price - 1))}"


def observation_view(row: dict) -> dict:
    return {
        "capture": row["source_file"], "line": row["source_line"], "role": row["source_role"],
        "fetched_at": row["fetched_at"], "source_day": row["source_day"] or None,
        "sport": row["sport"], "league_label": row["league_label"] or None,
        "path_prefix": row["prefix"] or None, "slug": row["slug"] or None,
        "market": row["market"] or None, "selection": row["consensus"] or None,
        "tips": row["tips"] or None, "note": row["note"] or None,
        "carry_note": row["carry_note"] or None,
        "tip_share_pct": int(row["tip_share"]) if row["tip_share"].isdigit() else None,
        "start_utc": row["start_utc"] or None, "date_label": row["date_label"] or None,
        "time_label": row["time_label"] or None, "event_title": row["event_title"] or None,
        "odds_decimal": numeric_or_none(row["odds_decimal"]),
        "odds_american": row["odds_american"] or None,
        "odds_fractional": row["odds_fractional"] or None,
        "event_url": row["event_url"], "listing_url": row["listing_url"] or None,
    }


def conflict_issues(observations: dict[str, list[dict]]) -> list[dict]:
    issues: list[dict] = []
    for event_id, rows in sorted(observations.items()):
        if len(rows) < 2:
            continue
        for field, code, severity, label in (
            ("start_utc", "capture_start_conflict", "warning", "OLBG startDate"),
            ("event_title", "capture_identity_conflict", "warning", "event title"),
            ("event_url", "capture_url_conflict", "warning", "event URL"),
            ("sport", "capture_sport_conflict", "error", "sport"),
            ("market", "capture_market_changed", "info", "headline market"),
            ("odds_decimal", "capture_price_changed", "info", "displayed decimal price"),
        ):
            def value(row):
                return numeric_or_none(row[field]) if field == "odds_decimal" else row[field]

            values = {value(row) for row in rows if row.get(field)}
            if len(values) > 1:
                issues.append(make_issue(
                    severity, code,
                    f"Event {event_id} has {len(values)} different {label} values across committed captures",
                    event_id=event_id, field=field,
                    observations=[source_reference(row) | {"value": value(row)} for row in rows if row.get(field)],
                ))
    return issues


def official_host_register(verifications: dict, official: dict, root_rows: list[dict]) -> set[str]:
    hosts: set[str] = set()

    def add(url_or_host: str | None):
        if not url_or_host:
            return
        host = urlparse(url_or_host).hostname if "://" in url_or_host else url_or_host
        if host:
            hosts.add(host.lower().removeprefix("www."))

    for source in verifications.get("sources", []):
        if source.get("class") in ("official", "primary"):
            add(source.get("url"))
    tiers = official.get("source_tiers", {})
    for tier in ("official", "club-official"):
        for host in tiers.get(tier, []):
            add(host)
    for row in root_rows:
        verification = row.get("verification") or {}
        if verification.get("source_tier") in ("official", "club-official"):
            add(verification.get("official_url"))
    return hosts


def is_official_url(url: str, hosts: set[str]) -> bool:
    host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    return bool(host and host in hosts and host != "olbg.com")


def trigram_similarity(first: str, second: str) -> float:
    def tokens(text: str) -> list[str]:
        text = re.sub(r"\b\d+(?:\.\d+)?\b", "#", text.lower())
        return re.findall(r"[a-z0-9]+(?:'[a-z]+)?", text)

    a, b = tokens(first), tokens(second)
    sa, sb = set(zip(a, a[1:], a[2:])), set(zip(b, b[1:], b[2:]))
    return len(sa & sb) / max(1, len(sa | sb))


def audit_prediction_track(
    track: str,
    predictions: list[dict],
    rows: dict[str, dict],
    adapters: dict,
    official_hosts: set[str],
    name_aliases: dict[str, str],
) -> tuple[list[dict], dict]:
    issues: list[dict] = []
    seen_ids: set[str] = set()
    seen_bodies: dict[str, str] = {}
    high_rows = {ref for ref, row in rows.items() if adapters["confidence"](row) == "high"}
    prediction_rows = {p[adapters["id"]] for p in predictions}
    for ref in sorted(high_rows - prediction_rows):
        issues.append(make_issue(
            "error", "high_prediction_missing", f"{track} HIGH row {ref} has no written prediction",
            track=track, match_id=ref, event_url=adapters["event_url"](rows[ref]),
        ))

    for prediction in predictions:
        ref = prediction[adapters["id"]]
        text = prediction.get(adapters["text"]) or ""
        selection = prediction.get("selection") or ""
        headline = prediction.get("headline") or ""
        status = str(prediction.get("status") or "high").lower()
        row = rows.get(ref)
        event_link = adapters["event_url"](row) if row else None
        base = {"track": track, "match_id": ref, "event_url": event_link}
        if ref in seen_ids:
            issues.append(make_issue("error", "prediction_id_duplicate", f"Duplicate {track} prediction {ref}", **base))
        seen_ids.add(ref)
        if row is None:
            issues.append(make_issue("error", "prediction_row_missing", f"{track} prediction {ref} has no board row", **base))
            continue
        confidence = adapters["confidence"](row)
        if confidence == "high" and status != "high":
            issues.append(make_issue(
                "error", "high_prediction_status_mismatch",
                f"{ref} is HIGH but its prediction status is {status!r}", **base,
            ))
        if confidence != "high" and status != "analysis":
            issues.append(make_issue(
                "error", "analysis_prediction_status_mismatch",
                f"{ref} is {confidence} but its prediction status is {status!r}", **base,
            ))
        word_count = len(text.split())
        if word_count < 30:
            issues.append(make_issue(
                "error", "prediction_too_short", f"{ref} prediction has {word_count} words; minimum is 30",
                word_count=word_count, **base,
            ))
        if not selection.strip():
            issues.append(make_issue("error", "prediction_selection_blank", f"{ref} has no explicit selection", **base))
        banned = BANNED_PREDICTION_TERMS.search(" ".join((selection, headline, text)))
        if banned:
            issues.append(make_issue(
                "error", "prediction_prohibited_term",
                f"{ref} reader-facing prediction contains prohibited term {banned.group(0)!r}", **base,
            ))
        sources = prediction.get("sources") or []
        if not sources:
            issues.append(make_issue("error", "prediction_sources_missing", f"{ref} has no source links", **base))
        urls: list[str] = []
        for source in sources:
            url = source.get("url") or ""
            urls.append(url)
            if urlparse(url).scheme != "https" or not urlparse(url).hostname:
                issues.append(make_issue(
                    "error", "prediction_source_url_invalid", f"{ref} has a malformed/non-HTTPS source: {url!r}",
                    source_url=url or None, **base,
                ))
            if not normalise_space(source.get("label")):
                issues.append(make_issue(
                    "warning", "prediction_source_label_blank", f"{ref} has a source link without a label",
                    source_url=url or None, **base,
                ))
        if confidence == "high":
            pick = adapters["pick"](row) or ""
            if not pick or not selection_names_pick(pick, selection, name_aliases):
                issues.append(make_issue(
                    "error", "high_prediction_selection_mismatch",
                    f"{ref} prediction selection does not name the published pick {pick!r}",
                    published_pick=pick or None, prediction_selection=selection or None, **base,
                ))
            if not MARKET_WORDS.search(selection):
                issues.append(make_issue(
                    "error", "high_prediction_market_unclear",
                    f"{ref} selection does not state a recognisable betting market: {selection!r}", **base,
                ))
            if not any(is_official_url(url, official_hosts) for url in urls):
                issues.append(make_issue(
                    "error", "high_prediction_official_source_missing",
                    f"{ref} HIGH prediction has no source on the repository's official/club-official register",
                    source_urls=urls, **base,
                ))
            release_source = adapters["release_source"](row)
            if release_source and release_source not in urls:
                issues.append(make_issue(
                    "warning", "release_source_not_listed_in_prediction",
                    f"{ref} release-evidence URL is not repeated in its prediction source list",
                    release_source=release_source, **base,
                ))
        body_key = normalise_space(text).lower()
        if body_key:
            if body_key in seen_bodies:
                issues.append(make_issue(
                    "error", "prediction_body_duplicate",
                    f"{ref} prediction duplicates {seen_bodies[body_key]} word for word",
                    duplicate_of=seen_bodies[body_key], **base,
                ))
            else:
                seen_bodies[body_key] = ref

    for first, second in itertools.combinations(predictions, 2):
        a = first[adapters["id"]]
        b = second[adapters["id"]]
        score = trigram_similarity(first.get(adapters["text"]) or "", second.get(adapters["text"]) or "")
        if score >= 0.30:
            both_high = first[adapters["id"]] in high_rows and second[adapters["id"]] in high_rows
            issues.append(make_issue(
                "warning" if both_high else "info", "prediction_near_duplicate_review",
                f"{a} and {b} share {score:.1%} of normalized word trigrams; review for repetitive prose",
                track=track, match_ids=[a, b], similarity=round(score, 4),
            ))
    return issues, {"predictions": len(predictions), "high_rows": len(high_rows)}


def build_report(root: Path = ROOT) -> dict:
    data_dir = root / "data"
    meta = load_json(data_dir / "meta.json")
    if not meta:
        raise FileNotFoundError(data_dir / "meta.json")
    matches = load_json(data_dir / "matches.json", [])
    lines = load_json(data_dir / "lines.json", [])
    verifications = load_json(data_dir / "verifications.json", {"sources": [], "event_verifications": {}})
    overrides = load_json(data_dir / "live_overrides.json", {"withdrawn": [], "updates": []})
    official = load_json(data_dir / "official.json", {"source_tiers": {}})
    publication = load_json(data_dir / "publication.json", {})
    root_events = load_json(data_dir / "events.json", {"events": []}).get("events", [])
    root_gap = load_json(data_dir / "gap_sports.json", {"rows": []}).get("rows", [])
    root_rows_list = root_events + root_gap
    root_predictions = load_json(data_dir / "predictions.json", {"predictions": []}).get("predictions", [])
    olbg_predictions = load_json(data_dir / "predictions-olbg.json", {"predictions": []}).get("predictions", [])

    issues: list[dict] = []
    observations, capture_errors, sources = read_captures(data_dir, meta)
    issues.extend(capture_errors)
    by_event: dict[str, list[dict]] = defaultdict(list)
    selected: dict[str, dict] = {}
    for row in observations:
        # Malformed rows stay visible as capture errors above, but cannot create a cascade of
        # fabricated UNK/blank publication identities in the lineage comparison.
        if not row["event_id"].isdigit() or row["sport_id"] is None:
            continue
        by_event[row["event_id"]].append(row)
        if row["event_id"] not in selected:
            selected[row["event_id"]] = row
    issues.extend(conflict_issues(by_event))

    source_register = verifications.get("sources", [])
    source_by_id: dict[str, dict] = {}
    for source in source_register:
        source_id = source.get("id")
        if not normalise_space(source_id):
            issues.append(make_issue(
                "error", "verification_source_id_blank", "Verification source register entry has a blank id",
                source_url=source.get("url"),
            ))
        if source_id in source_by_id:
            issues.append(make_issue(
                "error", "verification_source_id_duplicate", f"Duplicate verification source id {source_id!r}",
                source_id=source_id,
            ))
        source_by_id[source_id] = source
        if urlparse(source.get("url") or "").scheme != "https":
            issues.append(make_issue(
                "error", "verification_source_url_invalid", f"Verification source {source_id} lacks an HTTPS URL",
                source_id=source_id, source_url=source.get("url"),
            ))
    event_verifications = verifications.get("event_verifications", {})
    overrides_by_id = {
        update["match_id"]: update for update in overrides.get("updates", []) if update.get("match_id")
    }
    retired = {
        str(item.get("match_id") or item.get("olbg_event_id"))
        for item in overrides.get("withdrawn", [])
    }

    match_by_id: dict[str, dict] = {}
    for match in matches:
        match_id = match.get("id")
        if match_id in match_by_id:
            issues.append(make_issue("error", "published_match_id_duplicate", f"Duplicate published match {match_id}"))
        match_by_id[match_id] = match

    expected_by_id: dict[str, dict] = {}
    selected_source_by_id: dict[str, dict] = {}
    for event_id, source_row in selected.items():
        verification = event_verifications.get(event_id, {})
        provisional_id = f"{ID_PREFIX.get(source_row['sport'], 'UNK')}-{event_id}"
        expected = expected_match(source_row, verification, overrides_by_id.get(provisional_id))
        match_id = expected["id"]
        expected_by_id[match_id] = expected
        selected_source_by_id[match_id] = source_row
        if match_id in retired:
            if match_id in match_by_id:
                issues.append(make_issue(
                    "error", "withdrawn_match_still_published", f"Withdrawn row {match_id} remains published",
                    match_id=match_id, event_url=source_row["event_url"],
                ))
            continue
        actual = match_by_id.get(match_id)
        if actual is None:
            issues.append(make_issue(
                "error", "capture_row_missing_from_publication",
                f"Selected capture event {event_id} is absent from data/matches.json",
                match_id=match_id, **source_reference(source_row),
            ))
            continue
        for field, expected_value in expected.items():
            actual_value = actual.get(field)
            if actual_value != expected_value:
                issues.append(make_issue(
                    "error", "capture_publication_field_mismatch",
                    f"{match_id} field {field} differs from its selected capture/verification/override inputs",
                    match_id=match_id, field=field, expected=expected_value, actual=actual_value,
                    **source_reference(source_row),
                ))
        slug_name = source_row["slug"].replace("_", " ")
        if expected["event_name"] != slug_name and actual.get("olbg_event_name") != slug_name:
            issues.append(make_issue(
                "error", "capture_original_name_not_preserved",
                f"{match_id} has a display-name override but does not preserve the capture slug name",
                match_id=match_id, expected=slug_name, actual=actual.get("olbg_event_name"),
                **source_reference(source_row),
            ))
        source_classes = {
            source_by_id[source_id].get("class")
            for source_id in actual.get("verification_ids", []) if source_id in source_by_id
        }
        if actual.get("verification_status") in ("verified", "verified_market_row") and not (
            source_classes & {"official", "primary"}
        ):
            issues.append(make_issue(
                "error", "verified_row_without_official_register_source",
                f"{match_id} is marked verified but has no official/primary source-register entry",
                match_id=match_id, event_url=actual.get("olbg_url"),
            ))

    for match_id, actual in match_by_id.items():
        if match_id not in expected_by_id:
            issues.append(make_issue(
                "error", "published_match_has_no_selected_capture",
                f"Published row {match_id} has no row in the declared capture chain",
                match_id=match_id, event_url=actual.get("olbg_url"),
            ))
        for source_id in actual.get("verification_ids", []):
            if source_id not in source_by_id:
                issues.append(make_issue(
                    "error", "verification_source_id_unresolved",
                    f"{match_id} references missing verification source {source_id!r}",
                    match_id=match_id, source_id=source_id, event_url=actual.get("olbg_url"),
                ))

    line_by_id: dict[str, dict] = {}
    for line in lines:
        match_id = line.get("match_id")
        if match_id in line_by_id:
            issues.append(make_issue("error", "published_line_id_duplicate", f"Duplicate line {match_id}"))
        line_by_id[match_id] = line
    for match_id in sorted(set(match_by_id) - set(line_by_id)):
        issues.append(make_issue("error", "line_missing", f"{match_id} has no originated line", match_id=match_id))
    for match_id in sorted(set(line_by_id) - set(match_by_id)):
        issues.append(make_issue("error", "line_orphaned", f"Line {match_id} has no match row", match_id=match_id))

    for match_id, line in line_by_id.items():
        match = match_by_id.get(match_id)
        if not match:
            continue
        base = {"match_id": match_id, "event_url": match.get("olbg_url")}
        for field in ("sport", "event_name", "home", "away", "competition", "olbg_url"):
            if line.get(field) != match.get(field):
                issues.append(make_issue(
                    "error", "line_match_field_mismatch", f"{match_id} line field {field} differs from its match",
                    field=field, expected=match.get(field), actual=line.get(field), **base,
                ))
        expected_start = match.get("date_iso") or match.get("olbg_date_label")
        if line.get("start") != expected_start:
            issues.append(make_issue(
                "error", "line_start_mismatch", f"{match_id} line start differs from its match",
                expected=expected_start, actual=line.get("start"), **base,
            ))
        inputs = line.get("inputs") or {}
        for line_field, match_field in (
            ("olbg_market", "olbg_market"),
            ("olbg_consensus_selection", "olbg_consensus_selection"),
            ("olbg_tips", "olbg_tips"),
        ):
            if inputs.get(line_field) != match.get(match_field):
                issues.append(make_issue(
                    "error", "line_input_mismatch", f"{match_id} line input {line_field} differs from its match",
                    field=line_field, expected=match.get(match_field), actual=inputs.get(line_field), **base,
                ))
        probability = line.get("our_pick_probability")
        price = line.get("our_price_pick")
        if line.get("our_match_probability") != probability:
            issues.append(make_issue(
                "error", "line_match_probability_mismatch",
                f"{match_id} our_match_probability differs from our_pick_probability",
                expected=probability, actual=line.get("our_match_probability"), **base,
            ))
        tips_won, tips_total = match.get("olbg_tips_won"), match.get("olbg_tips_total")
        expected_raw = round(tips_won / tips_total, 4) if tips_won is not None and tips_total else None
        if inputs.get("p_raw") != expected_raw:
            issues.append(make_issue(
                "error", "line_raw_probability_mismatch",
                f"{match_id} inputs.p_raw does not recompute from the captured tip count",
                expected=expected_raw, actual=inputs.get("p_raw"), **base,
            ))
        if probability is not None and not 0 < probability < 1:
            issues.append(make_issue(
                "error", "line_probability_invalid", f"{match_id} pick probability is outside (0,1)",
                actual=probability, **base,
            ))
        if price is not None:
            if probability is None:
                issues.append(make_issue("error", "line_price_without_probability", f"{match_id} has a price but no probability", **base))
            else:
                expected_price = round(0.95 / probability, 2)
                if abs(price - expected_price) > 0.005:
                    issues.append(make_issue(
                        "error", "line_price_does_not_recompute",
                        f"{match_id} price {price} does not recompute from p={probability}: expected {expected_price}",
                        expected=expected_price, actual=price, **base,
                    ))
                expected_fair = round(1 / probability, 2)
                if line.get("our_fair_odds") != expected_fair:
                    issues.append(make_issue(
                        "error", "line_fair_odds_mismatch", f"{match_id} fair odds do not recompute",
                        expected=expected_fair, actual=line.get("our_fair_odds"), **base,
                    ))
                expected_us = decimal_to_american(price)
                if line.get("our_us_odds_pick") != expected_us:
                    issues.append(make_issue(
                        "error", "line_american_odds_mismatch", f"{match_id} US odds do not convert from decimal price",
                        expected=expected_us, actual=line.get("our_us_odds_pick"), **base,
                    ))
            if not line.get("our_pick"):
                issues.append(make_issue("error", "line_priced_without_pick", f"{match_id} has a price but no selection", **base))
        elif line.get("our_us_odds_pick") is not None or line.get("our_fair_odds") is not None:
            issues.append(make_issue("error", "line_unpriced_with_odds", f"{match_id} is unpriced but carries odds", **base))
        is_outright = match.get("market_family") == "outright" or match.get("sport") == "Greyhounds"
        expected_other = (
            round(0.95 / (1 - probability), 2)
            if probability is not None and 0 < probability < 1 and not is_outright else None
        )
        if line.get("our_price_other") != expected_other:
            issues.append(make_issue(
                "error", "line_other_price_mismatch",
                f"{match_id} opposing price does not recompute from the complementary probability",
                expected=expected_other, actual=line.get("our_price_other"), **base,
            ))
        if line.get("confidence") not in ("high", "medium", "low"):
            issues.append(make_issue(
                "error", "line_confidence_invalid", f"{match_id} has invalid confidence {line.get('confidence')!r}", **base,
            ))

    schema_text = (data_dir / "schema.md").read_text(encoding="utf-8") if (data_dir / "schema.md").exists() else ""
    semantic_rows = [
        line for line in lines
        if line.get("our_match_probability") is not None
        and line.get("our_match_probability") == line.get("our_pick_probability")
        and (match_by_id.get(line["match_id"], {}).get("olbg_consensus_selection") or "") != (line.get("our_pick") or "")
    ]
    if "probability of the **OLBG consensus selection**" in schema_text and semantic_rows:
        issues.append(make_issue(
            "warning", "schema_probability_semantics_conflict",
            "data/schema.md says our_match_probability describes the OLBG consensus selection, "
            "but generated rows set it equal to our_pick_probability even when the selection differs",
            affected_rows=[line["match_id"] for line in semantic_rows],
            source="data/schema.md#linesjson-fields",
        ))

    official_hosts = official_host_register(verifications, official, root_rows_list)
    name_aliases = load_name_aliases(root)
    olbg_adapters = {
        "id": "match_id", "text": "text",
        "confidence": lambda row: str(row.get("confidence") or "").lower(),
        "pick": lambda row: row.get("our_pick"),
        "event_url": lambda row: row.get("olbg_url"),
        "release_source": lambda row: (row.get("release") or {}).get("source"),
    }
    prediction_issues, olbg_prediction_summary = audit_prediction_track(
        "olbg", olbg_predictions, line_by_id, olbg_adapters, official_hosts, name_aliases,
    )
    issues.extend(prediction_issues)

    root_by_ref = {row["ref"]: row for row in root_rows_list}
    if len(root_by_ref) != len(root_rows_list):
        issues.append(make_issue(
            "error", "root_row_ref_duplicate", "Root board contains duplicate row refs",
            expected=len(root_rows_list), actual=len(root_by_ref),
        ))
    root_adapters = {
        "id": "ref", "text": "body",
        "confidence": lambda row: str((row.get("pick") or {}).get("confidence") or "").lower(),
        "pick": lambda row: (row.get("pick") or {}).get("label"),
        "event_url": lambda row: row.get("olbg_event_url"),
        "release_source": lambda row: ((row.get("pick") or {}).get("release") or {}).get("source"),
    }
    prediction_issues, root_prediction_summary = audit_prediction_track(
        "root", root_predictions, root_by_ref, root_adapters, official_hosts, name_aliases,
    )
    issues.extend(prediction_issues)

    root_body_map = {
        normalise_space(p.get("body")).lower(): p["ref"]
        for p in root_predictions if normalise_space(p.get("body"))
    }
    for prediction in olbg_predictions:
        body = normalise_space(prediction.get("text")).lower()
        if body and body in root_body_map:
            issues.append(make_issue(
                "warning", "cross_track_prediction_duplicate",
                f"{prediction['match_id']} duplicates root prediction {root_body_map[body]} word for word",
                match_id=prediction["match_id"], duplicate_of=root_body_map[body],
                event_url=(line_by_id.get(prediction["match_id"]) or {}).get("olbg_url"),
                sources=prediction.get("sources") or [],
            ))

    lineage = []
    for event_id in sorted(selected, key=lambda value: (0, int(value)) if value.isdigit() else (1, value)):
        source_row = selected[event_id]
        match_id = f"{ID_PREFIX.get(source_row['sport'], 'UNK')}-{event_id}"
        lineage.append({
            "event_id": event_id,
            "match_id": match_id,
            "selected_capture": source_row["source_file"],
            "selected_line": source_row["source_line"],
            "published": match_id in match_by_id,
            "withdrawn": match_id in retired,
            "observations": [observation_view(row) for row in by_event[event_id]],
        })

    severity_counts = Counter(issue["severity"] for issue in issues)
    selected_counts = Counter(row["source_file"] for row in selected.values())
    input_paths = [
        "meta.json", "publication.json", "matches.json", "lines.json", "verifications.json",
        "official.json", "live_overrides.json", "events.json", "gap_sports.json",
        "predictions.json", "predictions-olbg.json", "schema.md",
    ] + [source["file"] for source in sources]
    hashes = {
        path: sha256(data_dir / path)
        for path in dict.fromkeys(input_paths) if (data_dir / path).exists()
    }
    summary = {
        "status": "fail" if severity_counts["error"] else ("review" if severity_counts["warning"] else "pass"),
        "errors": severity_counts["error"], "warnings": severity_counts["warning"],
        "informational": severity_counts["info"],
        "capture_observations": len(observations), "distinct_capture_events": len(selected),
        "unselected_observations": len(observations) - len(selected),
        "published_matches": len(matches), "published_lines": len(lines),
        "selected_events_by_capture": dict(sorted(selected_counts.items())),
        "withdrawn_selected_events": sum(1 for match_id in expected_by_id if match_id in retired),
        "source_register_entries": len(source_register),
        "root_prediction_rows": root_prediction_summary,
        "olbg_prediction_rows": olbg_prediction_summary,
        "official_source_hosts_registered": len(official_hosts),
    }
    return {
        "schema_version": 1,
        "audit": "capture-to-publication provenance",
        "scope": (
            "Internal fidelity to committed captures, verification records, overrides, line arithmetic and prediction metadata. "
            "This report does not assert that any official sporting fact is current or that any linked page was retrieved during the audit."
        ),
        "publication_as_of": publication.get("publication_as_of"),
        "source_precedence": [source["file"] for source in sources],
        "input_sha256": hashes,
        "summary": summary,
        "issues": issues,
        "event_lineage": lineage,
    }


def markdown_text(value) -> str:
    return normalise_space(value).replace("|", "\\|")


def markdown_link(label: str, url: str | None) -> str:
    return f"[{markdown_text(label)}]({url})" if url else markdown_text(label)


def render_markdown(report: dict) -> str:
    """Render a concise human review index; the JSON remains the complete evidence record."""
    summary = report["summary"]
    issues = report["issues"]
    lines = [
        "# Capture-to-publication provenance audit",
        "",
        f"Publication clock audited: **{markdown_text(report.get('publication_as_of') or 'not stated')}**. "
        "This is a deterministic reread of committed files, not a fresh capture or a certification of current sporting facts.",
        "",
        f"**Result: {summary['status'].upper()} — {summary['errors']} errors, "
        f"{summary['warnings']} warnings, {summary['informational']} informational observations.**",
        "",
        "A clean lineage result means the published data can be reproduced from the declared inputs. "
        "It does not prove that an old listing is still available, that a start time is officially confirmed, "
        "or that a selection is advisable. Blank source values remain blank; conflicting observations remain visible.",
        "",
        "## Coverage",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Raw capture observations | {summary['capture_observations']} |",
        f"| Distinct captured events | {summary['distinct_capture_events']} |",
        f"| Observations not selected by first-capture-wins | {summary['unselected_observations']} |",
        f"| Published match rows accounted for | {summary['published_matches']} |",
        f"| Published originated-line rows accounted for | {summary['published_lines']} |",
        f"| Root written predictions / HIGH rows | {summary['root_prediction_rows']['predictions']} / {summary['root_prediction_rows']['high_rows']} |",
        f"| OLBG-board written predictions / HIGH rows | {summary['olbg_prediction_rows']['predictions']} / {summary['olbg_prediction_rows']['high_rows']} |",
        f"| Verification source-register entries | {summary['source_register_entries']} |",
        "",
        "## Method and precedence",
        "",
        "1. Read the primary, carried, and supplementary captures declared by `data/meta.json`, including both v2 and v3 layouts.",
        "2. Keep every observation with its raw path, line number, fetch time, listing URL, event URL, and all captured v3 fields.",
        "3. Replay the builder's first-capture-wins rule, then apply event verification fields, explicit live overrides, and withdrawals.",
        "4. Compare the reconstructed row with `matches.json`; compare every originated line with its match and recompute its price arithmetic.",
        "5. Check both prediction tracks for row/status agreement, explicit HIGH selections, source metadata, prohibited terms, release-evidence linkage, and repeated prose.",
        "6. Hash every input so another reviewer can tell whether a difference comes from the auditor or from changed data.",
        "",
        "The auditor performs no network requests. Official-host classification comes from the committed source register; "
        "it is not a fresh content check. Later capture values are not automatically superior, and a difference from OLBG consensus is not an error: "
        "editorial priors, fades, outright analysis, non-winner markets, and explicit overrides are legitimate parts of the publication chain.",
        "",
        "### Selected rows by capture",
        "",
        "| Capture | Selected events |",
        "|---|---:|",
    ]
    for capture in report["source_precedence"]:
        lines.append(f"| {markdown_link(capture, '../data/' + capture)} | {summary['selected_events_by_capture'].get(capture, 0)} |")

    clock = [issue for issue in issues if issue["code"] == "capture_start_conflict"]
    release = [issue for issue in issues if issue["code"] == "release_source_not_listed_in_prediction"]
    schema = [issue for issue in issues if issue["code"] == "schema_probability_semantics_conflict"]
    duplicates = [issue for issue in issues if issue["code"] == "cross_track_prediction_duplicate"]
    handled = {"capture_start_conflict", "release_source_not_listed_in_prediction",
               "schema_probability_semantics_conflict", "cross_track_prediction_duplicate"}

    lines.extend(["", "## Warnings for manual review", ""])
    if clock:
        lines.extend([
            "### Conflicting source clocks",
            "",
            "Both observations are retained. The selected publication value follows the declared first-capture-wins rule; "
            "the conflict is not silently resolved and no official start is inferred.",
            "",
        ])
        for issue in clock:
            lines.append(f"#### {markdown_link(issue['event_id'], issue['observations'][0].get('event_url'))}")
            lines.append("")
            for observation in issue["observations"]:
                raw = f"{observation['capture']}#L{observation['line']}"
                lines.append(
                    f"- **{markdown_text(observation.get('value') or 'blank')}** — "
                    f"{markdown_link(raw, '../data/' + raw)}, fetched {markdown_text(observation.get('fetched_at') or 'not stated')}; "
                    f"{markdown_link('OLBG event', observation.get('event_url'))}."
                )
            lines.append("")
        if {issue.get("event_id") for issue in clock} & {"32383", "32384", "32385", "32386"}:
            lines.extend([
                "Manual review lead for the European Championship rows: the "
                "[official PDC schedule announcement](https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/) "
                "was attempted, but the retrieved content contained cookie/privacy boilerplate rather than usable schedule evidence. "
                "It therefore does not resolve these clocks.",
                "",
            ])
    if release:
        lines.extend([
            "### HIGH release evidence absent from prediction source lists",
            "",
            "These rows have an official release-evidence URL on the board, but that exact URL is not repeated in the written prediction's source list. "
            "This is a transparency follow-up, not proof that the analysis is wrong. No citation has been invented or silently added.",
            "",
            "| Track | Match | Official release evidence | Listing |",
            "|---|---|---|---|",
        ])
        for issue in release:
            lines.append(
                f"| {markdown_text(issue.get('track'))} | {markdown_text(issue.get('match_id'))} | "
                f"{markdown_link('source', issue.get('release_source'))} | {markdown_link('OLBG event', issue.get('event_url'))} |"
            )
        lines.append("")
    for issue in schema:
        lines.extend([
            "### Probability-field semantics",
            "",
            markdown_text(issue["message"]).rstrip(".") + f". The report identifies **{len(issue.get('affected_rows', []))} affected rows**. "
            "The schema owner must choose and document the intended meaning; this audit does not rewrite either the schema or generated lines.",
            "",
            f"Review {markdown_link('data/schema.md', '../data/schema.md#linesjson-fields')} and "
            f"{markdown_link('data/lines.json', '../data/lines.json')}.",
            "",
        ])
    if duplicates:
        lines.extend([
            "### Repeated prose across dashboard tracks",
            "",
            "The same fixture can legitimately appear on both tracks, but word-for-word reuse still needs an editorial decision under the uniqueness requirement.",
            "",
            "| OLBG-board row | Root row | Official sources on the written piece | Listing |",
            "|---|---|---|---|",
        ])
        for issue in duplicates:
            source_links = "; ".join(
                markdown_link(source.get("label") or "source", source.get("url"))
                for source in issue.get("sources", [])
            ) or "not stated"
            lines.append(
                f"| {markdown_text(issue.get('match_id'))} | {markdown_text(issue.get('duplicate_of'))} | "
                f"{source_links} | {markdown_link('OLBG event', issue.get('event_url'))} |"
            )
        lines.append("")
    other_warnings = [
        issue for issue in issues
        if issue["severity"] == "warning" and issue["code"] not in handled
    ]
    if other_warnings:
        lines.extend(["### Other warnings", "", "| Code | Finding |", "|---|---|"])
        for issue in other_warnings:
            lines.append(f"| `{markdown_text(issue['code'])}` | {markdown_text(issue['message'])} |")
        lines.append("")
    if not any(issue["severity"] == "warning" for issue in issues):
        lines.extend(["No warnings in this snapshot.", ""])

    info_counts = Counter(issue["code"] for issue in issues if issue["severity"] == "info")
    lines.extend([
        "## Informational differences",
        "",
        "These differences are retained for review but are not publication errors by themselves. "
        "In particular, the builder does not overwrite an existing event when a later supplement changes its market or displayed price.",
        "",
        "| Code | Count | Meaning |",
        "|---|---:|---|",
    ])
    descriptions = {
        "capture_market_changed": "Nonempty headline-market labels differ across captures.",
        "capture_price_changed": "Displayed decimal prices differ across captures; no independent bookmaker price is inferred.",
        "prediction_near_duplicate_review": "Normalized word-trigram similarity merits a human prose review; it is not proof of duplication.",
    }
    for code, count in sorted(info_counts.items()):
        lines.append(f"| `{markdown_text(code)}` | {count} | {markdown_text(descriptions.get(code, 'See the machine-readable issue record.'))} |")
    if not info_counts:
        lines.append("| None | 0 | No informational differences in this snapshot. |")

    lines.extend([
        "",
        "## Review boundary and reproduction",
        "",
        "- No capture, fixture, verification, override, line, prediction, flag, or generated HTML file is modified by this audit.",
        "- The complete per-event observation chain and every issue's raw references are in "
        f"{markdown_link('data/provenance_audit.json', '../data/provenance_audit.json')}.",
        "- Quota coverage, current OLBG availability, and live deployment are separate release checks; this report does not certify them.",
        "",
        "Reproduce with:",
        "",
        "```bash",
        "python3 scripts/audit_provenance.py",
        "python3 -m unittest tests.test_audit_4e26d590",
        "```",
        "",
    ])
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root (default: this checkout)")
    parser.add_argument("--output", type=Path, default=None, help="report path (default: <root>/data/provenance_audit.json)")
    parser.add_argument("--markdown", type=Path, default=None, help="review index (default: <root>/docs/audit-4e26d590.md)")
    parser.add_argument("--no-write", action="store_true", help="run checks without writing either report")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    report = build_report(root)
    output = args.output or root / "data" / "provenance_audit.json"
    markdown = args.markdown or root / "docs" / "audit-4e26d590.md"
    if not args.no_write:
        output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        markdown.write_text(render_markdown(report), encoding="utf-8")
    print(json.dumps(report["summary"], indent=2))
    for issue in report["issues"]:
        if issue["severity"] == "error":
            print(f"ERROR {issue['code']}: {issue['message']}")
    if not args.no_write:
        print(f"Report: {output}")
        print(f"Review index: {markdown}")
    return 1 if report["summary"]["errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
