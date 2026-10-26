# October 26 refresh, research and integration — session-ef52c632

## Executive result

- New robots-aware listing capture: **142 distinct entries**, from 18 successful OLBG listing responses, **2026-10-26 20:20:26 UTC**. Snooker rendered no cards. This is not every market or every participant.
- Combined lines board: **523 rows**, including carry-only dated history; **520 winner/entrant estimates**, three left unpriced because the captured selection/market does not support a winner price.
- **Seven new original NHL analyses; two HIGH research-grade picks** (Rangers and Oilers), five analysis leans. All seven include >30 words, explicit selection, current official records, recent form and direct official source links. Injury and starting-goalie information was not established and no absence claim is made.
- Main shortlist: **2/75**, shortfall **73**; none of the 15 sports meets five. Missing facts, complete-market enumeration, independently measured probabilities and betting-platform acceptance remain unmet, not silently inferred.
- Existing historical prose remains labelled analysis. The separate next-day board is now subject to listing-observation expiry rather than retaining a HIGH label indefinitely.

## Retrieval and fact review

[Capture runner](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40394727276) succeeded. Evidence is in:
- `data/raw/live-20261026T2020Z-ef52c632/`: robots policy, HTML, rendered text, status and digest per response, extraction report.
- `data/raw/official-20261026T2021Z/`: official structured schedules/standings and text pages, including explicit HTTP failures.
- `data/raw/cited-20261026T2022Z/`: reread of previously cited pages, including byte-faithful EHF PDF. Retrieval is not automatic fact certification.

[Pricing and field-level fact receipts](pricing-ef52c632.md) link the official NHL schedule and standings used in each new analysis. The schedule matching requires both teams and an exact league UTC start within the documented listing tolerance. Seven NHL listings are seven minutes later than the league clocks; official clocks govern publication. One MLB fixture also matched the official schedule, but no unsupported baseball write-up was created.

| Sport | New captured entries | Official manual-review destination |
| --- | ---: | --- |
| Golf | 3 | [PGA Tour schedule](https://www.pgatour.com/schedule) |
| Volleyball | 15 | [Volleyball World](https://en.volleyballworld.com/volleyball/competitions/volleyball-national-leagues/schedule/) — 404 |
| Rugby Union | 13 | [URC fixtures](https://www.unitedrugby.com/fixtures) — 404 |
| Cricket | 17 | [ICC fixtures](https://www.icc-cricket.com/fixtures-results) |
| Snooker | 0 | [WST matches](https://www.wst.tv/matches/) |
| Darts | 2 | [PDC tournaments](https://www.pdc.tv/tournaments) — consent page, not confirmed fixtures |
| Baseball | 1 | [MLB schedule](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-26&endDate=2026-10-28&hydrate=team,linescore,probablePitcher) |
| Gaelic Football | 3 | [GAA fixtures](https://www.gaa.ie/fixtures-results) |
| Greyhounds | 8 | [GBGB racecard](https://www.gbgb.org.uk/racecard) — 404 |
| Tennis | 20 | [ATP scores](https://www.atptour.com/en/scores/current) — 403; [WTA scores](https://www.wtatennis.com/scores) |
| Motor Racing | 2 | [Formula 1 calendar](https://www.formula1.com/en/racing/2026) |
| Handball | 17 | [EHF calendar](https://www.eurohandball.com/en/calendar/) |
| Ice Hockey | 11 | [NHL schedule](https://api-web.nhle.com/v1/schedule/2026-10-26) |
| Basketball | 27 | [NBA schedule](https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json) — 403; [EuroLeague games](https://www.euroleaguebasketball.net/en/euroleague/games/) — 429 |
| Rugby League | 3 | [Super League fixtures](https://www.superleague.co.uk/fixtures) — 500 |

Counts come from captured OLBG rows, not from the official destinations. A destination link is not a claim that its contents confirm every OLBG row. No row was promoted simply because a request returned HTTP 200.

## Repairs and automation

1. Four-hour robots-aware retrieval schedule, separate from hourly HTML rebuild. Immutable timestamped paths; failed rebase no longer masked. GitHub schedules are best-effort, not a realtime feed.
2. New captures become the primary dataset before pricing; every prior source remains in dated carry-only order. Empty captures cannot erase the board.
3. Official verification IDs now identify the actual probe rather than reusing October 23 IDs. Old source records are preserved.
4. Nested sport pages link correctly to Flagged for Review when stale.
5. Zero-pick builds are supported. Historical tests no longer demand that a live HIGH pick always exist. Synthetic positive and negative eligibility tests preserve gate coverage.
6. Expired Utah price removed from current-facing historical analysis, original retained in archive field; source facts not renewed.

Review flags **FL-232–237** are published on both review registers. The reproducible internal provenance audit (`data/audit-ef52c632.json`, [review index](audit-ef52c632-provenance.md)) reports errors separately from clock conflicts and assumption warnings; it does **not** claim a live official reread of all historical rows.

## Validation and publication

Local: 430 unit tests, 26 dated skips; board integrity, independent prediction quality, site validation, official-feed validation and local-link checks. Publication receipts are recorded in COORDINATION.md after remote checks and deployment. No claim of full user-brief completion is made: every-sport daily original analysis, complete OLBG market discovery and calibrated independent pricing remain gaps.
