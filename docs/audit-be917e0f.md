# Audit — `session-be917e0f`, daily capture 2026-10-23 (task-47)

This pass captured all fifteen in-scope OLBG sport listings on **2026-10-23 between 16:05Z and 16:20Z**, re-observed
the official clocks that today's live picks depend on, added the captured fixtures to the board, and republished the
site. It did **not** re-date, re-quote or re-verify anything it did not read: every earlier observation keeps its own
`checked_at`, and rows whose observation is now more than 24 hours old are archived as analysis by the shared release
gate rather than silently refreshed.

## 1. Capture

* File: `data/raw/olbg-harvest-20261023T1620Z.json` (format v3-json; every label verbatim, no clock converted).
* Method: agent page retrieval of `/Tennis/3`, `/Basketball/4`, `/Golf/5`, `/Cricket/7`, `/Snooker/8`,
  `/Rugby_Union/9`, `/Rugby_League/10`, `/Baseball/12`, `/Ice_Hockey/13`, `/Motor_Racing/14`, `/Darts/15`,
  `/Handball/20`, `/Volleyball/21`, `/Gaelic_Football/25`, `/Greyhounds/28`.
* 107 rows captured, **0 excluded-sport rows**. 50 were appended to `data/sports/*.json` as previously uncaptured
  events, 55 were already on the board (same OLBG event id — not duplicated), 2 greyhound races sit on the
  outright/race track which has no per-sport capture file.
* Applier: `scripts/apply_capture.py` (new, generic). It copies names, date+time label, market, most-tipped
  selection, tip counts and the exact event URL; it derives only the internal `ref` (`<PREFIX>-<event_id>`) and writes
  the capture date onto each row so `Today`/`Tomorrow` can never be resolved against the wrong day.

## 2. Official observations made in this pass

| # | Source (official) | What was read | Result |
|---|---|---|---|
| 1 | `https://api-web.nhle.com/v1/schedule/2026-10-23` | gameweek payload, game 2026020166 | Montreal Canadiens at Chicago Blackhawks, United Center, `startTimeUTC 2026-10-24T00:00:00Z`, `gameState FUT` |
| 2 | same payload, game 2026020167 | Tampa Bay Lightning at Colorado Avalanche, Ball Arena, `2026-10-24T01:00:00Z` | recorded for completeness; OLBG did not render this fixture in today's cut, so it is **not** priced |
| 3 | `https://statsapi.mlb.com/api/v1/schedule?sportId=1&date=2026-10-23` | gamePk 849805 | World Series Game 1, Tampa Bay Rays at Milwaukee Brewers, American Family Field, `gameDate 2026-10-24T00:00:00Z` |
| 4 | `https://api-web.nhle.com/v1/standings/2026-10-22` (already committed) | club records used for form | Montreal 9 GP 4-3-2, 10 pts, 30-34, road 1-1-1; Chicago 9 GP 3-6-0, 6 pts, 21-36, home 3-2-0 |
| 5 | `https://stats.unitedrugby.com/match-centre/table/2026-27` | re-read | the standings table itself did not render through this client (image/lazy-loaded cells); **no value was taken from it** |

Sources that were attempted and returned nothing usable in this environment: `pdc.tv` tournament page (cookie wall),
`en.volleyballworld.com/.../superlega-2026/schedule/` (404), `legavolley.it/calendario-superlega/` (old article),
`gaacork.ie/fixtures/` (renders fixtures but prints `16:00` with **no zone label**, so it cannot certify a UTC start).

## 3. Release-gate consequences (published honestly, not hidden)

The publication clock advanced from `2026-10-22T22:10Z` to **`2026-10-23T16:45Z`** (the newest observation committed
today). Under the existing rules that has three effects, all of them visible on the site:

1. Fixtures dated 22 or 23 October now report `past_date` / `start_window_reached` and their picks are archived as
   analysis — the evidence grade (`HIGH`) and the written piece are kept, the live label is not.
2. Observations older than 24 hours report `stale_source` for the same reason. 23 root rows and part of the `/olbg/`
   track move into this state today.
3. Only rows with an observation newer than the clock **and** a start still ahead stay live.

Result at this build: **5 live root HIGH picks** (Baseball `BSB-01`, Ice Hockey `IHO-199984`, Volleyball `VOL-27`,
`VOL-28`, `VOL-29`) and **5 live `/olbg/` high picks**, a union of **8** — against the brief's 75-a-day target
(5 × 15 sports), a shortfall of **67** that `brief.html` recomputes from the rows and itemises per sport.

The mechanical reasons are the same as yesterday's and are not a modelling choice: golf had no listing at all today
(FL-132), rugby league has no fixture (FL-133), snooker's two matches had already started, tennis/handball/darts
listings print bare clocks with no zone, and 49 of today's new rows have no official source read yet (FL-135).

## 4. Verification performed

* `python3 -m unittest discover -s tests` → **109 tests, OK** (8 date-pinned assertions from earlier sessions were
  re-expressed as evidence invariants; the graded/archived state is what changed, not any price, source or word count).
* `scripts/check_board.py` → **PASS**: `rows=345 fixtures=297 outright_or_race=48 verified=247 priced=305 predictions=79`.
* `tools/check_site.py` → **PASS**: `pages=21 fixtures=338 lines=338 high=5 predictions=94 flagged=128`.
* `scripts/check.py` → **PASS** (40 feed rows). `scripts/check_links.py` → **PASS** (`0` broken of 2,367 local links).
* `scripts/brief_coverage.py` recomputes: `live HIGH root=5 olbg=5 union=8 shortfall=67`;
  cross-track `paired=247 agree=199 differ=21 withheld=27`; prose `root=79` (`HIGH 5`, min 57 words), `olbg=94`.

## 5. Irregularities raised this pass

| Flag | What | Where it shows |
|---|---|---|
| FL-132 | Golf listing rendered `No tips found.` at 16:12Z | Flagged for Review, brief coverage |
| FL-133 | Rugby League listing carries only 2027 outrights | Flagged for Review, brief coverage |
| FL-134 | Greyhound race-card time disagrees with the listing clock by ~5 h | Flagged for Review; rows not boarded |
| FL-135 | 49 new fixtures publish unverified, blank official fields | Flagged for Review; pinned in `tests/test_audit_d3464fe4.py` |
| FL-136 | NBA rows cannot be graded HIGH (no official NBA form input) | Flagged for Review, brief coverage |
| FL-137 | 78 earlier pieces still use the words "model"/"verified" | Flagged for Review (editorial) |

## 6. What this pass did **not** do

* It did not certify any start from a bare OLBG clock, and it did not convert a clock whose zone the source does not
  print (Tennis, Darts, Handball, Gaelic, Greyhounds).
* It did not re-price or rewrite another session's evidence, and it did not delete an expired row: expired rows remain
  published as dated analysis.
* It did not touch the `/olbg/` lines track inputs (`data/meta.json["harvest_file"]` still names the 21:30Z TSV); that
  track was rebuilt from its own committed inputs so the two tracks stay independent.

## 7. Collision handling at merge (recorded, not hidden)

While this pass ran, `session-c4cde934` also claimed a task numbered 46 and merged PRs #120/#121 into `main` (its own
2026-10-23 freshness audit, which expired the 22-October HIGH picks and registered its own `FL-131`). Neither pass was
discarded: this branch was reset onto `main` `46bdf7e`, **only the net-new work was re-applied** (the 16:20Z capture and
the 50 appended fixtures, the three fresh clocks, the `statsapi.mlb.com` allowlist entry, the NHL name aliases, the
`IHO-199984` piece and register items), this task was renumbered **`task-47`**, and this pass's six register items were
renumbered **`FL-132`..`FL-137`** so `FL-131` stays the other session's. The two sessions' test changes were merged
rather than overwritten: `session-c4cde934`'s `test_no_expired_high_on_olbg_track` now bounds the live-high count
instead of pinning 17, because the count moves with each day's observations.

