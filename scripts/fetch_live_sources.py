#!/usr/bin/env python3
"""Fetch public OLBG listing HTML for an auditable live-capture artifact.

This script only retrieves source pages. It does not alter verified data, originate
prices, or publish a site. The caller reviews the downloaded HTML before importing
any value into a dated raw harvest.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import time
import urllib.error
import urllib.request

PAGES = {
    "tennis": "https://www.olbg.com/betting-tips/Tennis/3",
    "basketball": "https://www.olbg.com/betting-tips/Basketball/4",
    "basketball-nba": "https://www.olbg.com/betting-tips/Basketball/NBA/4",
    "golf": "https://www.olbg.com/betting-tips/Golf/5",
    "cricket": "https://www.olbg.com/betting-tips/Cricket/7",
    "snooker": "https://www.olbg.com/betting-tips/Snooker/8",
    "rugby-union": "https://www.olbg.com/betting-tips/Rugby_Union/9",
    "rugby-league": "https://www.olbg.com/betting-tips/Rugby_League/10",
    "baseball": "https://www.olbg.com/betting-tips/Baseball/12",
    "ice-hockey": "https://www.olbg.com/betting-tips/Ice_Hockey/13",
    "ice-hockey-nhl": "https://www.olbg.com/betting-tips/Ice_Hockey/NHL/13",
    "motor-racing": "https://www.olbg.com/betting-tips/Motor_Racing/14",
    "darts": "https://www.olbg.com/betting-tips/Darts/15",
    "handball": "https://www.olbg.com/betting-tips/Handball/20",
    "volleyball": "https://www.olbg.com/betting-tips/Volleyball/21",
    "gaelic-football": "https://www.olbg.com/betting-tips/Gaelic_Football/25",
    "greyhounds": "https://www.olbg.com/betting-tips/Greyhounds/28",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("live-capture"))
    parser.add_argument("--only", action="append", choices=sorted(PAGES))
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    selected = args.only or list(PAGES)
    started = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    records = []
    for index, slug in enumerate(selected):
        url = PAGES[slug]
        request = urllib.request.Request(url, headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/130.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "en-GB,en;q=0.9",
        })
        record = {"slug": slug, "url": url}
        try:
            with urllib.request.urlopen(request, timeout=45) as response:
                body = response.read()
                record.update(status=response.status, bytes=len(body),
                              final_url=response.geturl(), content_type=response.headers.get("Content-Type"))
                (args.output / f"{slug}.html").write_bytes(body)
        except Exception as exc:  # retain every failure in the evidence artifact
            record.update(error=f"{type(exc).__name__}: {exc}")
        records.append(record)
        print(json.dumps(record), flush=True)
        if index + 1 < len(selected):
            time.sleep(1)
    completed = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    (args.output / "summary.json").write_text(json.dumps({
        "started_utc": started.isoformat().replace("+00:00", "Z"),
        "completed_utc": completed.isoformat().replace("+00:00", "Z"),
        "records": records,
    }, indent=2) + "\n")
    return 1 if any("error" in record or record.get("status") != 200 for record in records) else 0


if __name__ == "__main__":
    raise SystemExit(main())
