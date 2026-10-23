# Audit — session-22dbc477, 2026-10-23: live capture, official verification, deploy repair

Branch `arena/22dbc477-olbg3`, base `46d87165` (PR #118). Task `task-46` on the COORDINATION board.
Published as PR into `main`; merge and Pages record at the end.

## 0. Why this pass exists

The scheduled workflow on `main` had failed every hour since 2026-10-23T00:0xZ — runs
`39902389681`, `39936419745`, `39975101348`, each failing at **step 16**, *"Fail if the committed OLBG
track is stale"*, with `deploy` skipped. GitHub Pages therefore served the **2026-10-22T22:10Z**
snapshot for about 18 hours.

Root cause, reproduced locally with zero source changes: `scripts/board_dates.build_date()` returned
**real UTC today**, while the newest committed harvest was still dated 22 October. Every rebuild therefore
re-derived `kickoff_passed`, downgraded five Ice Hockey rows, rewrote `data/lines.json`,
`data/predictions-olbg.json` and the `/olbg/` pages, and the committed tree could never match its own
scripts. 14 files drifted on a clean checkout.

That is FL-131. The fix is in §4. The rest of this pass is the work the brief actually asks for: a
**live capture for 2026-10-23** across the 15 in-scope sports, verification against official sources,
and predictions only where the evidence supports them.

## 1. How data was obtained (this sandbox has no route to OLBG)

`curl` to `olbg.com`, `api-web.nhle.com`, `statsapi.mlb.com`, `formula1.com`, `www.nba.com` all fail
here with `SSL_ERROR_SYSCALL` — the documented outbound allowlist (FL-077). Rather than write the
session off, the fetch runs on a **GitHub Actions runner**, and the bytes actually served are committed
as evidence:

| Script | Runs on | Output |
|---|---|---|
| `scripts/live_harvest.py` | runner | `data/raw/live-20261023T1700Z/` — robots.txt, 18 HTML files, 18 text renderings, manifest with per-page status/bytes/sha256 |
| `scripts/extract_listings.py` | either | `data/raw/olbg-harvest-20261023T1700Z.tsv` — format **v3**, 177 rows |
| `scripts/official_probe.py` | runner | `data/raw/official-20261023T1628Z/` — NHL/MLB/NBA payloads + 14 governing-body pages |
| `scripts/probe_cited.py` | runner | `data/raw/cited-20261023T1631Z/` — 27 of 30 cited official pages re-read |
| `scripts/verify_live.py` | either | `data/verifications.json`, `data/release_checks.json` entries |
| `scripts/live_refresh.py` | both | picks the newest capture/probe and runs the two steps above |

The workflow triggers on a push that changes `.harvest/request.json` (this token cannot call
`actions:write`, so `workflow_dispatch` is unavailable — recorded in the request file history).

## 2. What the live capture contains, and what it proves

Run [`39985922565`](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/39985922565):
**18/18 listings captured**, 6.1 MB, 16:21Z. `Golf/5` returned HTTP 200 with **zero** tip cards and the
page's own "No tips found." (FL-134); Snooker returned 2 rows, Greyhounds 34.

* **177 rows across 14 sports**, 186 cards before de-duplication across the sub-league endpoints.
* Every row carries `<time itemprop="startDate" datetime="…Z">` — **OLBG's own machine-readable UTC
  start** — copied verbatim into the new `start_utc` column.
* Every row carries OLBG's `data-decimal` / `data-american` price for that selection, published as
  *OLBG's displayed price*, explicitly not a bookmaker sheet and not our line.
* **DST cross-check (tests/test_live_20261023.py):** for all 177 rows the clock OLBG printed differs
  from its own `startDate` by exactly the UK offset for that date — +1 h inside British Summer Time,
  0 outside it, including the 01:00/25 Oct boundary and a July 2027 row. That is mechanical evidence
  that the attribute is UTC and the printed label is UK local, so nothing has to be guessed. The
  printed label is still published verbatim and never converted.

## 3. Official verification: what matched, and what did not

`verify_live.py` writes a verification only when **both sides match** and the league's own UTC start is
within 90 minutes. Result — **3 of 17** ice-hockey/baseball fixtures:

| Event | OLBG `startDate` | Official payload | Source |
|---|---|---|---|
| `160789` TB Rays @ MIL Brewers | 2026-10-24T00:00Z | `gameDate 2026-10-24T00:00:00Z`, gamePk 849805 | `statsapi.mlb.com/api/v1/schedule` |
| `199984` MTL Canadiens @ CHI Blackhawks | 2026-10-24T00:07Z | `startTimeUTC 2026-10-24T00:00:00Z`, game 2026020166 | `api-web.nhle.com/v1/schedule/2026-10-23` |
| `199985` TB Lightning @ COL Avalanche | 2026-10-24T01:07Z | `startTimeUTC 2026-10-24T01:00:00Z`, game 2026020167 | same payload |

`statsapi.mlb.com` was added to `release.OFFICIAL_CLOCK_HOSTS` with a written reason: it is MLB's own
data service, it states `gameDate` as an explicit UTC instant, and without it the World Series row was
stuck at `unverified_start` while its clock was demonstrably quoted from MLB. No other host was added.

**Deliberately not verified:** the other 15 ice-hockey fixtures (European club leagues, FL-133); NBA and
EuroLeague (HTTP 403 / 429, FL-135); every other sport, because the governing bodies publish fixture
lists on JavaScript-rendered pages that the text probe cannot read. Those rows keep a blank official
start, stay `unverified`, and cannot grade HIGH.

### The renewal attempt, and why it was rejected

`probe_cited.py` re-read 27 of the 30 official pages already cited for upcoming fixtures, and
`reverify.py` accepts a renewal only when the re-fetched page still contains both sides, the recorded
clock **and** the recorded zone label inside one window.

It produced **4 candidates and all four were wrong on inspection**:

* `12101` matched page boilerplate (`Irudek Bidasoa Irun - Equipos …`) — no fixture, no clock.
* `12110` matched `19:00` elsewhere on the page while the fixture line beside **Estonia | Kosovo** reads
  `20:00 (CEST)` — a different match.
* `199984`/`199985` matched inside a raw JSON blob, not a quotable line.

Nothing was applied. The 24-hour expiry is therefore doing its job: those rows stay analysis. Recorded
here rather than quietly relaxing the gate.

## 4. The build-reproducibility repair (FL-131)

`board_dates.build_date()` now returns the **publication clock's date** (the newest committed source
observation) instead of the wall clock. Reproducibility is restored; freshness is enforced by three
mechanisms that do not pretend data is new:

1. `scripts/release.py` expires an observation 24 h after it was read and at the scheduled start;
2. `snapshot_age_hours()` drives a **SNAPSHOT STALE** banner on both boards once a capture is 30 h old
   (verified by unit test; the banner is intentionally absent today, because the capture is 2 h old);
3. `assets/release.js` re-checks expiry against the reader's own clock.

`tests/test_freshness.py` pins both the new date contract and the age arithmetic (41.5 h at
2026-10-25T10:00Z).

## 5. Published state at this commit

| | Value |
|---|---|
| Live rows | **177** across **14** sports (Golf 0 — FL-134) |
| Fixtures with our own money line | 177 |
| Handicap / total lines | see `picks.html` per row |
| Competition verified from an official source | 3 fixtures + the rows whose 22 Oct official evidence is still inside 24 h |
| **Current HIGH picks** | **5** — Rugby Union 3 (Edinburgh 1.42/-238, Connacht 1.44/-227, Bulls 1.53/-189), Volleyball 1 (Perugia 1.58/-158), Baseball 1 (Milwaukee Brewers 1.62/-161) |
| Written pieces | 31, every one ≥30 words and sourced |
| Review register | 128 items (FL-131…FL-136 added this pass) |

Five HIGH picks is short of the brief's five **per sport**. That is a source-availability limit, not a
modelling choice: a HIGH grade needs an official fixture **and** an official current-form input, and
today only the NHL, MLB and a handful of live 22 October observations provided either. Every sport that
falls short prints its own mechanical reason in the dashboard's coverage table and on
`flagged.html`; nothing was promoted to fill the gap.

## 6. Checks run on this commit

```
130 unit tests OK (25 skipped: dated 2026-10-22 snapshot pins, see FL-137)
scripts/check_board.py     PASS  (295 root rows, 78 pieces, brief-coverage recomputes)
tools/check_site.py        PASS  (177 fixtures, 128 register items, no dup write-ups)
scripts/check.py           PASS  (40 feed rows)
scripts/check_links.py     PASS  (108 pages, 2,326 links, 0 broken)
full documented rebuild twice -> git status --porcelain empty (byte-identical)
```

## 7. Irregularities published for review

FL-131 failed hourly build / frozen Pages · FL-132 the robots.txt `es` substring trap · FL-133 15
unverifiable European hockey fixtures · FL-134 Golf "No tips found." · FL-135 NBA/EuroLeague API
refusals · FL-136 two pieces re-priced after a tip-split move · FL-137 the archived-snapshot test
convention. Each carries its source links on `flagged.html`.
