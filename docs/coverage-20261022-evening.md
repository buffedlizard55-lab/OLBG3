# Per-sport coverage and certification audit — 2026-10-22 21:20Z

Session `session-cab97f19`. This file records, sport by sport, what the live OLBG listings actually
offered on the evening of 22 October 2026, what could be confirmed against an official source, and
where the "five highest-confidence picks per sport" target could not be met honestly.

Method and boundaries:

- Listings were read live through the agent page-retrieval tool between **20:53Z and 21:12Z** on
  2026-10-22 (`data/raw/olbg-harvest-20261022T2100Z.tsv`, 88 rows). The agent shell cannot reach
  sports sites directly (outbound allowlist covers GitHub and package registries only).
- A row is **verified** only when a governing body, league or club-official page names the fixture.
  A row is **eligible** for a `HIGH` grade only when the same evidence states an explicitly
  timezone-qualified start that is still ahead of the build clock (`scripts/release.py`).
- Nothing in the table below is inferred. Blank means the source did not state it.

## Counts at the 21:20Z publication clock

`/olbg/` track, `data/matches.json` + `data/lines.json`. "Certified upcoming" counts rows whose
certified official start is ahead of the clock; a listed fixture without a zoned official clock is
*not* counted here even when it is plainly in the future.

| Sport | Rows held | Verified | Certified upcoming | Live HIGH |
|---|---:|---:|---:|---:|
| Tennis | 53 | 45 | 0 | 0 |
| Basketball | 46 | 42 | 6 | 3 |
| Golf | 10 | 10 | 0 | 0 |
| Cricket | 18 | 15 | 2 | 1 |
| Snooker | 17 | 17 | 0 | 0 |
| Rugby Union | 18 | 16 | 1 | 1 |
| Rugby League | 3 | 2 | 0 | 0 |
| Baseball | 1 | 1 | 1 | 1 |
| Ice Hockey | 28 | 25 | 12 | 5 |
| Motor Racing | 4 | 4 | 0 | 0 |
| Darts | 17 | 17 | 2 | 2 |
| Handball | 40 | 31 | 0 | 0 |
| Volleyball | 41 | 30 | 4 | 3 |
| Gaelic Football | 6 | 5 | 1 | 1 |
| Greyhounds | 22 | 0 | 0 | 0 |
| **Total** | **324** | **254 verified + 6 market rows** | **29** | **17** |

## Why seven sports have no live HIGH pick

| Sport | Status tonight | Reason (not a modelling choice) |
|---|---|---|
| Tennis | 14 fixtures listed for 23 Oct | Official ATP/WTA order-of-play pages state a local start time without naming a zone (already recorded as FL-096/FL-097). No UTC start can be certified, so every tennis row publishes as verified analysis. |
| Handball | 15 fixtures listed, mostly French StarLigue | The official LNH calendar publishes bare local clocks; the `/calendrier` page had to be located under `/daikin-starligue/calendrier`, and no zoned clock could be certified in this pass. |
| Snooker | No fixtures | OLBG returned "No tips found." at 21:07Z (FL-100). |
| Rugby League | 3 rows held | No upcoming fixture on the evening listing; the captured Super League rows are past-date. |
| Golf | 10 rows | Listing is tournament outright markets (field priors), not two-sided matches. |
| Motor Racing | 4 rows | Formula 1 / qualifying outright and race markets, not two-sided matches. |
| Greyhounds | 22 rows | Race cards could not be confirmed against an official operator page; all stay unverified (FL-055/FL-095). |

## What five-per-sport would need

- **Ice Hockey** already carries five: the twelve NHL games on 2026-10-22 are certified to the second
  by `api-web.nhle.com/v1/schedule/2026-10-22` and five of them clear the model's HIGH gates.
- **Basketball** reaches three (Zalgiris, Boston, San Antonio) from the NBA's explicit `ET` clocks and
  the EuroLeague game already certified at midday. Two more would need either an official zoned clock
  for the EuroLeague round-8 games or model probabilities above the 0.55 floor.
- **Volleyball** reaches three from the officially certified Italian SuperLega fixtures; the four new
  Polish/Brazilian/German/Austrian fixtures listed at 21:09Z are unverified and cannot be graded.
- **Tennis, Handball, Cricket, Rugby Union, Darts** are capped by the number of fixtures whose
  official clock is both stated *and* zoned. Certifying more requires the leagues to publish zoned
  clocks, not more modelling.

## Irregularities raised by this pass

`FL-099` frozen publication clock (fixed), `FL-100` snooker listing empty, `FL-101` 25 of 26 new
fixtures uncertifiable, `FL-102` the availability table above, `FL-103` darts per-match clocks behind
a pdc.tv consent wall, `FL-104` nba.com missing from the reviewed clock allowlist (fixed).
