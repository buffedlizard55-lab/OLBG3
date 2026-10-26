# 2026-10-26 current-source refresh audit — `session-61e1daf3`

## Scope and result

At 2026-10-26 05:15–05:18 UTC, requested a new robots-aware OLBG listing capture and the configured official-source probes. The runner captured all 18 configured listing routes (including NBA/European Basketball and NHL subroutes) with HTTP 200 and recorded the bytes, timestamps and hashes in `data/raw/live-20261026T0515Z-61e1daf3/manifest.json`. OLBG `robots.txt` returned HTTP 200. The raw evidence is committed on this branch by harvest run [40273261391](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40273261391), commit `c412d8a`.

The deterministic extractor found **98 listed rows across 13 sports**, not a complete 15-sport set. It found no cards on the Golf or Snooker pages. It found 20 Tennis, 17 Basketball, 16 Volleyball, 13 Handball, 12 Cricket, 9 Ice Hockey, 3 Rugby League, 3 Gaelic Football, and one each in Baseball, Darts, Greyhounds, Motor Racing and Rugby Union. The raw OLBG pages are the source for listed entries, not official confirmation of the fixtures or their details.

The refresh was **not promoted as a new published prediction set**. A local deterministic rebuild against the current committed source observations yielded zero currently releasable HIGH picks at publication time 05:18Z (and 54 written pieces retained as analysis). This is a release-gate result, not a claim that no sporting selection could ever be recommended. No current injury, form, market price, or match statistic has been invented to fill the requested five-per-sport target.

## Official-source probe — line-by-line outcome

The probe manifest is `data/raw/official-20261026T0516Z/manifest.json`; verbatim payloads and rendered text are in its sibling files. Only successful responses are listed below as fetched; a successful HTTP response is not itself a confirmation of a specific fixture.

| Scope | Official URL | Outcome | Review note |
|---|---|---|---|
| NHL schedule | [NHL API schedule, 26 Oct](https://api-web.nhle.com/v1/schedule/2026-10-26) | HTTP 200 | Captured JSON, 47 games with start times. Three OLBG games matched and their NHL start times were 7 minutes earlier than OLBG's printed clocks; do not substitute the OLBG clock for the league clock. |
| NHL standings | [NHL API standings, 26 Oct](https://api-web.nhle.com/v1/standings/2026-10-26) | HTTP 200 | Captured. The pipeline's exact fixture and release checks produced four schedule-linked records; no new prose was certified in this pass. |
| MLB schedule | [MLB Stats API schedule, 26–28 Oct](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-26&endDate=2026-10-28&hydrate=team,linescore,probablePitcher) | HTTP 200 | Captured, three games. One matched OLBG event, with a one-hour time difference; requires event-level review before use. |
| MLB standings | [MLB Stats API standings, 2026](https://statsapi.mlb.com/api/v1/standings?leagueId=103,104&season=2026&date=2026-10-26&hydrate=team) | HTTP 200 | Captured response has an empty `records` array; it supplies no standings facts for a prediction. |
| NBA schedule | [NBA CDN schedule](https://cdn.nba.com/static/json/staticData/scheduleLeagueV2_1.json) | HTTP 403 | No NBA schedule facts confirmed. |
| Tennis | [ATP scores](https://www.atptour.com/en/scores/current) / [WTA scores](https://www.wtatennis.com/scores) | ATP HTTP 403; WTA HTTP 200 | WTA page captured; no claim that it confirmed a particular OLBG row. |
| Cricket | [ICC fixtures and results](https://www.icc-cricket.com/fixtures-results) | HTTP 200 | Captured text; no fixture-level promotion made. |
| Snooker | [World Snooker Tour matches](https://www.wst.tv/matches/) | HTTP 200 | Captured text; no fixture-level promotion made. |
| Rugby Union | [United Rugby Championship fixtures](https://www.unitedrugby.com/fixtures) | HTTP 404 | Configured official URL unavailable; no fixture-level confirmation. |
| Rugby League | [Super League fixtures](https://www.superleague.co.uk/fixtures) | HTTP 500 | Official endpoint error; no fixture-level confirmation. |
| Darts | [PDC tournaments](https://www.pdc.tv/tournaments) | HTTP 200 | Response parsed to zero text characters; HTTP success is not evidence of a readable fixture list. |
| Handball | [EHF calendar](https://www.eurohandball.com/en/calendar/) | HTTP 200 | Captured text; no fixture-level promotion made. |
| Volleyball | [Volleyball World schedule](https://en.volleyballworld.com/volleyball/competitions/volleyball-national-leagues/schedule/) | HTTP 404 | Configured URL unavailable; no fixture-level confirmation. |
| Gaelic Football | [GAA fixtures and results](https://www.gaa.ie/fixtures-results) | HTTP 200 | Captured text. Capture scope is Gaelic Football; it does not establish full coverage of Gaelic Sports. |
| Motor Racing | [Formula 1 2026 calendar](https://www.formula1.com/en/racing/2026) | HTTP 200 | Captured text; no race market or participant facts promoted. |
| Golf | [PGA Tour schedule](https://www.pgatour.com/schedule) | HTTP 200 | Captured text despite no OLBG cards in the captured Golf listing; no match/pick created. |
| Basketball | [EuroLeague games](https://www.euroleaguebasketball.net/en/euroleague/games/) | HTTP 429 | No EuroLeague fixture facts confirmed. |
| Greyhounds | [GBGB racecard](https://www.gbgb.org.uk/racecard) | HTTP 404 | Configured official URL unavailable; no race-level confirmation. |

Cited-source rereads captured the NHL schedule, an EHF match page and the EHF playing-times PDF byte-faithfully, plus the PDC page. These are archived under `data/raw/cited-20261026T0517Z/`; they are retrieval evidence, not automatic re-certification of older claims.

## Data irregularities for review

1. **Listing/parser gaps:** the capture extractor reports zero tip cards on OLBG Golf and Snooker; one Cricket tips parse gap and three Gaelic Football market parse gaps. See `data/raw/live-20261026T0515Z-61e1daf3/run.log` and `manifest.json`. No missing row or market was guessed.
2. **Clock differences:** the fresh NHL schedule matched three OLBG event IDs with start clocks 7 minutes apart; the MLB schedule matched one OLBG event whose listed and official clocks differ by one hour. Both official schedules provide their own clock; review the exact OLBG event details before changing displayed fixtures or releases.
3. **Scope ambiguity:** OLBG capture labels the GAA route Gaelic Football. It does not prove that every sport included by the broad phrase “Gaelic Sports” is covered.
4. **Official endpoint failures/empty content:** NBA HTTP 403, ATP HTTP 403, URC HTTP 404, Super League HTTP 500, Volleyball World HTTP 404, EuroLeague HTTP 429, GBGB HTTP 404; PDC returned HTTP 200 but no extracted text. These are retrieval blockers, not evidence that no matches exist.
5. **Coverage target:** the capture has 98 rows across 13 sports, while the request is five written predictions per sport (75 total). Only source-supported, upcoming, eligible fixtures can count; the shortfall must not be hidden by recycling expired picks or fabricating facts.
6. **Validation gate:** live workflow `Verify and publish dashboard` run [40273261500](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/40273261500), started from request commit `3bbb6ef` concurrently with the capture, failed in “Rebuild the OLBG lines track.” Its log download endpoint returned EOF in this environment. Replaying the full build locally succeeded through board/site checks, but the 422-test suite had 18 failures: historical tests still expected now-expired HIGH entries and old pick-surface content after the release clock advanced. The failures were not suppressed and the regenerated tree was not committed. Fix the time-sensitive tests against the frozen evidence/release instant before proposing publication.

## Verification boundary

The capture was checked from its committed manifest and runner logs; the official probe results above were checked row by row against the official-probe manifest. The local pipeline was replayed through `scripts/publication_clock.py`, `scripts/update.py`, `scripts/discovery.py`, `scripts/build.py`, `scripts/build_gap_sports.py`, `scripts/model.py`, `scripts/live_refresh.py`, `tools/build_dataset.py`, `tools/originate.py`, `scripts/brief_coverage.py`, `scripts/build_site.py`, `scripts/check_board.py`, `tools/build_site.py`, and `tools/check_site.py`. Board and site checks passed; `scripts/check.py` and `scripts/check_links.py` passed in the replay; the complete unit suite did not pass as recorded above. Local generated pages/data were discarded after diagnosis so a failing build is not represented as a verified release.

**No PR was opened or merged, and no GitHub Pages deployment was claimed.** This refresh has not passed the repository's complete CI gate.
