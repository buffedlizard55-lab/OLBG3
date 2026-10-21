# OLBG Research Desk

Independent, source-first sports dashboard. **Partial implementation, not a full betting service.** Not affiliated with OLBG. No validated picks or originated lines are published.

## Website
https://buffedlizard55-lab.github.io/OLBG3/

## Run locally
Python 3.12, standard library only:

```sh
python scripts/update.py
python -m unittest discover -s tests -v
python scripts/build.py
python scripts/check.py
python -m http.server 8000 --bind 0.0.0.0 --directory site
```

## Evidence and update design
- Hourly GitHub Actions refresh on main, with static Pages deployment and 14-day raw-source evidence artifacts. No credentials or manual data entry.
- Upcoming seven-day UTC window; NHL coverage limited to the week the API returns. NBA and MLB are league-level, not comprehensive sport coverage.
- Each fixture's participants/time/status are extracted from the linked official JSON feed. Raw payloads are saved under `data/evidence/` and archived by the workflow, not committed to Git.
- Failures produce explicit unverified coverage entries; stale fixture rows are not carried forward. Snapshot timestamp and two-hour stale warning are visible on all pages.
- Generated site is not tracked. `data/current.json` is a bootstrap snapshot only; workflow refreshes it in its workspace and publishes the fresh result as `site/data.json`.
- No source endpoint's success proves full coverage. No unofficial match or copied OLBG community tip is represented as independently verified information.
- Blank betting lines, form, history, selections and confidence are deliberate. There is no trained/calibrated model, official historical-result ingestion or narrative generator. Full sport/league coverage, market modeling and evidence-based narrative generation remain unfinished and flagged on the site.

## Sources
- https://api-web.nhle.com/v1/schedule/now
- https://statsapi.mlb.com/api/v1/schedule
- https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json
- https://www.olbg.com/betting-tips — inspected for structure, not an official fixture authority. Main page exposes popular community tips, event paths and event IDs; no undocumented/private API, bypass or copied editorial content is used.

## Validation boundaries
Unit tests cover parsing, missing fields, exclusions and HTML escaping. Build validation checks all local links, official fixture source hosts, unique fixture IDs and empty unsupported prediction fields. It does not assert that every external link is reachable, that official feed data is error-free, or that all events have been discovered. Additional sports reference links are candidates, not live-validated sources. Deployment and audit notes are in COORDINATION.md.
