# 2026-10-26 expiry and publication audit — session b3eff127

## Executive result

At the 2026-10-26T20:20:00Z publication clock, the newest committed OLBG observation (2026-10-24T22:25:15Z) is about 46 hours old. All former HIGH releases are therefore expired or started. The dashboard now says **0 current HIGH picks** and presents the retained prose as archived analysis. No fixture, price, statistic, injury, result, or source-check timestamp was renewed or inferred.

## Defect repaired

The stale-snapshot banner used a top-level `flagged.html` link on pages under `olbg-board/sports/`. Once the capture crossed the 30-hour stale threshold, all 14 generated sport pages therefore contained a broken internal link and the scheduled Pages workflow failed in `tools/check_site.py` before tests. `tools/build_site.py` now computes that banner link from page depth. A regression test checks both the top-level and every emitted sport page.

The prior live-pick tests were date pins written while 24–25 October fixtures were upcoming. Sixteen test methods still required a nonempty current HIGH set, fixed kickoff values, or current-pick markup after those releases had legitimately expired. Those explicitly historical live-state methods are now skipped with an expiry reason; durable pricing, source, prose, accounting, and link tests continue to run. The suite reports 424 tests with 42 dated skips.

## Existing official evidence retained

No external observation was made in this sandbox. Existing row-level official links remain on the dashboard and in `data/verifications.json` / `data/release_checks.json`, including the NHL schedule service (<https://api-web.nhle.com/>), MLB Stats API (<https://statsapi.mlb.com/>), and competition sources listed on each row. Their stored check times were not altered.

## Verification

- `python -m unittest discover -s tests -v`: 424 tests OK, 42 dated skips.
- `python scripts/check.py`: PASS.
- `python scripts/check_links.py`: 143 pages, 2,689 local links, 0 broken.
- `python scripts/check_board.py`: PASS; 367 rows, 319 fixtures, 0 current HIGH.
- `python tools/check_site.py`: PASS; 418 lines-track fixtures, 0 current HIGH.
- `git diff --check`: PASS.

## Irregularities / review

- The user target is 75 current written picks (five in each of 15 sports); this build truthfully has zero because no committed listing/source observation is current enough. Quotas were not filled by invention.
- The newest lines-track capture contains rows in 12 sports and the combined historical board contains 15 categories. Only 14 lines-track sport subpages are emitted because Golf currently has no row in that dataset; Golf remains represented on the main dashboard and shortfall accounting.
- A fresh OLBG capture was not possible from the sandbox's restricted network. The site labels the snapshot stale rather than presenting archived work as today's advice.
