# Scope

## Excluded (as instructed)

Soccer / football · American football · Boxing · UFC / MMA · Hurling · Horse racing · Cycling · Specials (TV, politics, awards).

## Included (15 sports, 137 rows)

| Sport | Rows | Of which outright/race |
|---|---|---|
| Tennis | 14 | 0 |
| Basketball | 14 | 0 |
| Ice Hockey | 7 | 0 |
| Cricket | 9 | 0 |
| Baseball | 1 | 0 |
| Volleyball | 15 | 0 |
| Darts | 14 | 0 |
| Snooker | 6 | 0 |
| Rugby Union | 15 | 0 |
| Rugby League | 3 | 3 |
| Handball | 15 | 0 |
| Gaelic Football | 5 | 1 |
| Golf | 10 | 10 |
| Motor Racing | 3 | 3 |
| Greyhounds | 6 | 6 |

114 rows are two-sided fixtures; 23 are outright or race markets. Rugby League has no dated match on OLBG at
capture time — only 2027 futures — so it contributes three outright rows and no fixture row.

## Gap that used to exist here, now closed

The previous build listed Golf · Motor racing · Greyhound racing as "eligible but not captured". None of them
is in the exclusion list, so they were a coverage hole, not a scope decision. They were re-read from OLBG at
07:05Z on 2026-10-21 and are now published:

* `data/raw/gap_sports_capture_20261021.json` — verbatim capture (23 rows, listing URLs, assumptions)
* `scripts/build_gap_sports.py` — one-selection pricing model
* `data/gap_sports.json` — generated rows on the board

Esports remains uncaptured: no esports listing surfaced on the OLBG tips index at capture time. That is
disclosed rather than guessed at.

## Ambiguities that are included and flagged

| Item | Why it is included | Where it is flagged |
|---|---|---|
| Gaelic football | The exclusion list says "football" and "hurling" but not Gaelic football | Flagged for Review, `data/meta.json` |
| Greyhound racing | "Horse racing" is excluded; greyhound racing is a different sport | Flagged for Review |
| Motor racing | "Cycling" is excluded; motor racing is not named | Flagged for Review |

## Row count and verification status

137 rows · 11 verified against an official competition source · 126 published unverified with the OLBG event
link attached. Every row is on the board; none is silently dropped.

## Rules applied to every cell

| Rule | Applied how |
|---|---|
| No inference | Competition, venue and time zone are left blank when OLBG does not state them. |
| No rounding of official values | Official wording is copied verbatim into `data/official.json` and onto the verification page. |
| Discrepancies are logged, not fixed | The 7–10 minute start-time offset between OLBG and official schedules is recorded as a finding. |
| Nothing verified without a fixture-level link | 11 rows carry an official link that actually shows the fixture; the rest are `unverified` and blank. A competition homepage is not accepted as proof (see the legacy-draft finding). |
| Our prices are ours | Every price is labelled model output, never a bookmaker quote. |
| A one-selection market is not a fixture | Outright/race rows carry one originated price and no handicap or total, and say so in the Market column. |
