#!/usr/bin/env python3
"""Independent prose-quality checks for written predictions on both tracks.

The established board/site checkers remain authoritative for the 30-word floor,
price quotes, confidence/status agreement, release eligibility, source URL syntax,
and exact duplicates within each track.  This checker deliberately adds the missing
rules instead of replacing or weakening those checks:

* a HIGH prediction's selection and body must endorse the row's actual pick;
* the exact words ``model`` and ``verified`` are forbidden in prediction prose;
* a HIGH prediction must cite at least two distinct, reviewed official documents;
* near-duplicates are detected across both tracks (and within a track), with
  analysis-only pairs reported for review and any pair involving HIGH blocked; and
* a deterministic per-pick manifest can be written for audit evidence.

No network access, sporting inference, price calculation, or data rewriting occurs.
"""
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urldefrag, urlsplit

ROOT = Path(__file__).resolve().parents[1]
PROHIBITED_WORDS = ("model", "verified")
OFFICIAL_CLASSES = {"official", "primary"}
# OLBG is the listing/crowd source, not an official sporting body.  The other
# exclusions are reviewed secondary/reference outlets that can occur in the source
# registry; neither may satisfy the official-document requirement.
NON_OFFICIAL_HOSTS = {
    "www.olbg.com",
    "www.cricinfo.com",
    "www.snooker.org",
    "www.sportsgambler.com",
    "scores24.live",
    "www.espn.com",
    "www.cbssports.com",
    "apnews.com",
    "en.wikipedia.org",
    "news.sbs.co.kr",
    "www.bbc.com",
    "www.bbc.co.uk",
}
SHINGLE_SIZE = 4
JACCARD_THRESHOLD = 0.60
SEQUENCE_THRESHOLD = 0.92

# Short club/team abbreviations and generic words are not useful identity evidence.
ENTITY_STOPWORDS = {
    "club", "team", "county", "city", "united", "football", "rugby", "basketball",
    "handball", "volley", "hockey", "racing", "winner", "win", "match", "money",
    "line", "outright", "race", "sport", "sports", "association", "universite",
}
ENDORSEMENT = re.compile(
    r"\bback\b|\btake\b|\bselect\b|\bplay\b|"
    r"\bour\s+(?:selection|pick|call|play|lean|preference)\b|"
    r"\b(?:is|are|remains?|remain)\s+(?:the|our)\s+"
    r"(?:selection|pick|call|play|money-line\s+lean)\b|"
    r"\bto\s+win\b|\bwe\s+(?:take|back|prefer|favou?r|support)\b|"
    r"\bmoney-line\s+(?:selection|lean|call)\b|"
    r"\bthe\s+(?:selection|pick|play)\b",
    re.IGNORECASE,
)
NO_SELECTION = re.compile(r"^no\s+(?:selection|originated\s+selection)\b", re.IGNORECASE)


@dataclass
class QualityReport:
    errors: list[str]
    warnings: list[str]
    manifest: dict[str, Any]

    @property
    def ok(self) -> bool:
        return not self.errors


def _json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _words(text: str) -> list[str]:
    ascii_text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    return re.findall(r"[a-z0-9]+", ascii_text.lower())


def _entity_text(text: str) -> str:
    # Removing apostrophes (rather than turning them into spaces) makes dAix and
    # d'Aix comparable.  Accents and punctuation never become identity evidence.
    ascii_text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode()
    ascii_text = ascii_text.lower().replace("'", "")
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def _anchors(text: str) -> set[str]:
    return {
        token for token in _entity_text(text).split()
        if len(token) >= 4 and token not in ENTITY_STOPWORDS
    }


def _contains_entity(text: str, entity: str) -> bool:
    normalised_text = _entity_text(text)
    full_entity = _entity_text(entity)
    if full_entity and full_entity in normalised_text:
        return True
    return any(
        re.search(rf"\b{re.escape(anchor)}\b", normalised_text)
        for anchor in _anchors(entity)
    )


def _selection_subject(selection: str) -> str:
    first_part = (selection or "").split(";", 1)[0].strip()
    subject = re.split(
        r"\s+(?:to\s+win\b|money\s*line\b|match\s+winner\b|"
        r"outright(?:\s+winner)?\b|race\s*\()",
        first_part,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    return subject.strip(" (,-")


def _sentences(body: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", body or "") if part.strip()]


def _canonical_url(url: str) -> str:
    """Canonicalise only for diversity counting; fragments do not make new documents."""
    defragmented, _ = urldefrag((url or "").strip())
    parsed = urlsplit(defragmented)
    if not parsed.scheme or not parsed.hostname:
        return defragmented
    host = parsed.hostname.lower()
    if host == "www.olbg.com":
        # Explicitly retained as a valid non-official listing URL.
        pass
    path = parsed.path.rstrip("/") or "/"
    netloc = host
    if parsed.port and not (
        (parsed.scheme.lower() == "https" and parsed.port == 443)
        or (parsed.scheme.lower() == "http" and parsed.port == 80)
    ):
        netloc = f"{host}:{parsed.port}"
    return urlsplit(defragmented)._replace(
        scheme=parsed.scheme.lower(), netloc=netloc, path=path, fragment=""
    ).geturl()


def _official_hosts(root: Path) -> set[str]:
    registry = _json(root / "data" / "verifications.json")
    hosts = set()
    for source in registry.get("sources", []):
        if source.get("class") not in OFFICIAL_CLASSES:
            continue
        host = urlsplit(source.get("url", "")).hostname
        if host:
            host = host.lower()
            if host not in NON_OFFICIAL_HOSTS:
                hosts.add(host)
    return hosts


def _load_records(root: Path) -> list[dict[str, Any]]:
    root_predictions = _json(root / "data" / "predictions.json").get("predictions", [])
    root_rows = {}
    for filename, key in (("events.json", "events"), ("gap_sports.json", "rows")):
        for row in _json(root / "data" / filename).get(key, []):
            root_rows[row.get("ref")] = row

    olbg_predictions = _json(root / "data" / "predictions-olbg.json").get("predictions", [])
    lines = {
        line.get("match_id"): line
        for line in _json(root / "data" / "lines.json")
    }

    records = []
    for prediction in root_predictions:
        ref = prediction.get("ref", "")
        row = root_rows.get(ref) or {}
        records.append({
            "track": "root",
            "ref": ref,
            "status": prediction.get("status", "high"),
            "selection": prediction.get("selection") or "",
            "headline": prediction.get("headline") or "",
            "body": prediction.get("body") or "",
            "sources": prediction.get("sources") or [],
            "row_pick": (row.get("pick") or {}).get("label") or "",
            "has_row": bool(row),
        })
    for prediction in olbg_predictions:
        ref = prediction.get("match_id", "")
        line = lines.get(ref) or {}
        records.append({
            "track": "olbg",
            "ref": ref,
            "status": prediction.get("status", "high"),
            "selection": prediction.get("selection") or "",
            "headline": "",
            "body": prediction.get("text") or "",
            "sources": prediction.get("sources") or [],
            "row_pick": line.get("our_pick") or "",
            "has_row": bool(line),
        })
    return sorted(records, key=lambda item: (item["track"], item["ref"]))


def _shingles(words: list[str]) -> set[tuple[str, ...]]:
    if len(words) < SHINGLE_SIZE:
        return {tuple(words)} if words else set()
    return {
        tuple(words[index:index + SHINGLE_SIZE])
        for index in range(len(words) - SHINGLE_SIZE + 1)
    }


def _similarity(left: list[str], right: list[str]) -> tuple[float, float]:
    left_shingles, right_shingles = _shingles(left), _shingles(right)
    union = left_shingles | right_shingles
    jaccard = len(left_shingles & right_shingles) / len(union) if union else 1.0
    sequence = difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    return jaccard, sequence


def run_quality_gate(root: Path | str = ROOT) -> QualityReport:
    """Return all quality findings and a deterministic manifest for ``root``."""
    root = Path(root)
    records = _load_records(root)
    official_hosts = _official_hosts(root)
    errors: list[str] = []
    warnings: list[str] = []
    manifest_picks: dict[tuple[str, str], dict[str, Any]] = {}
    word_cache: dict[tuple[str, str], list[str]] = {}

    for record in records:
        key = (record["track"], record["ref"])
        prefix = f"quality {record['track']}/{record['ref']}"
        status = record["status"]
        body = record["body"]
        selection = record["selection"]
        words = _words(body)
        word_cache[key] = words

        prohibited = []
        for field, text in (
            ("headline", record["headline"]),
            ("selection", selection),
            ("body", body),
        ):
            for word in PROHIBITED_WORDS:
                if re.search(rf"\b{re.escape(word)}\b", text or "", re.IGNORECASE):
                    prohibited.append(f"{field}:{word}")
                    errors.append(f"{prefix}: prohibited word {word!r} in {field} prediction prose")

        official_urls = set()
        source_hosts = set()
        for source in record["sources"]:
            if not isinstance(source, dict):
                continue
            url = source.get("url", "")
            host = urlsplit(url).hostname
            if host:
                host = host.lower()
                source_hosts.add(host)
                if host in official_hosts:
                    official_urls.add(_canonical_url(url))

        selection_check = "not_applicable_analysis"
        diversity_check = "not_applicable_analysis"
        if status == "high":
            selection_check = "pass"
            if not record["has_row"]:
                selection_check = "fail"
                errors.append(f"{prefix}: HIGH prediction has no published row/pick to agree with")
            elif NO_SELECTION.match(selection.strip()) or not record["row_pick"]:
                selection_check = "fail"
                errors.append(f"{prefix}: HIGH prediction does not name a concrete row selection")
            else:
                selection_matches = _contains_entity(selection, record["row_pick"])
                if not selection_matches:
                    selection_check = "fail"
                    errors.append(
                        f"{prefix}: prediction selection does not agree with row pick "
                        f"{record['row_pick']!r}"
                    )
                # The written selection supplies harmless full-name aliases for abbreviated
                # row labels (for example, MIL Brewers -> Milwaukee Brewers). It is considered
                # only when row/selection agreement passed, so it cannot legitimise a swap.
                aliases = record["row_pick"]
                if selection_matches:
                    aliases = f"{aliases} {_selection_subject(selection)}"
                if not any(
                    ENDORSEMENT.search(sentence) and _contains_entity(sentence, aliases)
                    for sentence in _sentences(body)
                ):
                    selection_check = "fail"
                    errors.append(
                        f"{prefix}: body does not explicitly endorse row pick "
                        f"{record['row_pick']!r}"
                    )

            diversity_check = "pass" if len(official_urls) >= 2 else "fail"
            if len(official_urls) < 2:
                errors.append(
                    f"{prefix}: HIGH prediction has {len(official_urls)} distinct reviewed "
                    "official document(s); at least 2 are required"
                )

        manifest_picks[key] = {
            "track": record["track"],
            "id": record["ref"],
            "status": status,
            "word_count": len(body.split()),
            "meets_existing_30_word_floor": len(body.split()) >= 30,
            "body_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
            "selection_body_agreement": selection_check,
            "prohibited_terms": sorted(prohibited),
            "official_source_diversity": diversity_check,
            "official_document_count": len(official_urls),
            "official_document_urls": sorted(official_urls),
            "all_source_hosts": sorted(source_hosts),
            "near_duplicates": [],
        }

    # Compare globally: the pre-existing exact-body checks only see one track at a time.
    for left_index, left in enumerate(records):
        left_key = (left["track"], left["ref"])
        left_words = word_cache[left_key]
        if not left_words:
            continue
        for right in records[left_index + 1:]:
            right_key = (right["track"], right["ref"])
            right_words = word_cache[right_key]
            if not right_words:
                continue
            if left["track"] == right["track"] and left_words == right_words:
                # Exact duplicates within one track are already release-blocking in the
                # established checker; do not emit a second copy of that same rule.
                continue
            jaccard, sequence = _similarity(left_words, right_words)
            if jaccard < JACCARD_THRESHOLD and sequence < SEQUENCE_THRESHOLD:
                continue
            involves_high = "high" in (left["status"], right["status"])
            severity = "error" if involves_high else "warning"
            detail = {
                "track": right["track"],
                "id": right["ref"],
                "shingle_jaccard": round(jaccard, 6),
                "sequence_ratio": round(sequence, 6),
                "severity": severity,
            }
            reverse_detail = {
                "track": left["track"],
                "id": left["ref"],
                "shingle_jaccard": round(jaccard, 6),
                "sequence_ratio": round(sequence, 6),
                "severity": severity,
            }
            manifest_picks[left_key]["near_duplicates"].append(detail)
            manifest_picks[right_key]["near_duplicates"].append(reverse_detail)
            message = (
                f"quality near-duplicate {left['track']}/{left['ref']} <-> "
                f"{right['track']}/{right['ref']} "
                f"(4-word Jaccard={jaccard:.3f}, sequence={sequence:.3f})"
            )
            (errors if involves_high else warnings).append(message)

    ordered_picks = []
    for key in sorted(manifest_picks):
        entry = manifest_picks[key]
        entry["near_duplicates"].sort(key=lambda item: (item["track"], item["id"]))
        ordered_picks.append(entry)

    manifest = {
        "schema_version": 1,
        "rules": {
            "selection_body_agreement": "HIGH predictions",
            "prohibited_whole_words": list(PROHIBITED_WORDS),
            "prohibited_word_scope": ["headline", "selection", "body"],
            "high_min_distinct_official_documents": 2,
            "official_source_classes": sorted(OFFICIAL_CLASSES),
            "non_official_hosts": sorted(NON_OFFICIAL_HOSTS),
            "near_duplicate_shingle_words": SHINGLE_SIZE,
            "near_duplicate_jaccard_threshold": JACCARD_THRESHOLD,
            "near_duplicate_sequence_threshold": SEQUENCE_THRESHOLD,
            "analysis_near_duplicate_severity": "warning",
            "existing_checks_not_replaced": [
                "30-word floor", "source URL syntax", "price quotes",
                "confidence/status agreement", "release eligibility",
                "exact duplicates within each track",
            ],
        },
        "counts": {
            "predictions": len(records),
            "high": sum(record["status"] == "high" for record in records),
            "analysis": sum(record["status"] == "analysis" for record in records),
            "errors": len(errors),
            "warnings": len(warnings),
        },
        "picks": ordered_picks,
    }
    return QualityReport(errors=errors, warnings=warnings, manifest=manifest)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="repository root")
    parser.add_argument("--manifest", type=Path, help="write deterministic JSON audit manifest")
    args = parser.parse_args(argv)

    report = run_quality_gate(args.root)
    if args.manifest:
        args.manifest.parent.mkdir(parents=True, exist_ok=True)
        args.manifest.write_text(
            json.dumps(report.manifest, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    counts = report.manifest["counts"]
    print(
        "written-pick quality: "
        f"predictions={counts['predictions']} high={counts['high']} "
        f"analysis={counts['analysis']} errors={counts['errors']} warnings={counts['warnings']}"
    )
    for warning in report.warnings:
        print(f"  WARN {warning}")
    for error in report.errors:
        print(f"  FAIL {error}")
    if report.errors:
        print(f"FAIL: {len(report.errors)} written-pick quality violation(s)")
        return 1
    print("PASS: HIGH selections agree with their rows and bodies, official documents are diverse, "
          "prohibited prose terms are absent, and no HIGH near-duplicates were found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
