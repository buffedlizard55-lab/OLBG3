# Session `1c6981d1` — 2026-10-24: one page that answers "what is the pick, and where is it?"

Task: `task-1c6981d1` (claim at the top of [`COORDINATION.md`](../COORDINATION.md), branch
`arena/1c6981d1-olbg3`). Scope: the executive summary / landing-page clarity work, the 17:11Z
re-harvest, and the test pins that broke when that harvest moved the board.

## The complaint this session is answering

> "The sites are too confusing to understand what the matches are and where the picks are."

Two line-origination pipelines and ~110 published pages is a lot of surface, and nothing on the
site said which page carried today's selections. The site now has a **single merged answer**:

* `summary.html` — *"Executive summary"* — is the second item in the navigation on every page and
  the first call to action on the landing page. It lists every released HIGH pick for today and
  the next seven days, one row per fixture, with **the selection in its own column**, our price
  in decimal and US odds, the confidence, and the official source the fixture was confirmed
  against. The full reasoning for each pick follows in the same page under **The reasoning**,
  at least 30 words each, with the sources it rests on.
* The landing page (`index.html`) repeats today's picks and the next seven days in the same table
  shape, then the per-sport coverage grid, then a **Where to find everything** map. A reader who
  lands cold sees the picks before the coverage arithmetic.
* The two tracks are **merged and de-duplicated on the OLBG event id**, so a fixture that both
  pipelines price appears once. Where the two pipelines disagree, both selections stay published
  and the cross-track review page links them.
* `data/exec_summary.json` is the single data source for both pages, and
  `scripts/check_exec_summary.py` re-derives every number it prints (`check_board.py` alone could
  not: it validates the rows, not the summary's arithmetic).

## What the board says at the 2026-10-24T17:14:00Z publication clock

19 released HIGH picks across **8 of the 15 covered sports** — 8 today, 11 in the next seven days.
Two sports meet the five-a-day target (Ice Hockey 5, Handball 5); the other six that carry a pick
are one to three short. Nothing below is claimed as a proven edge: our prices are our own
originated lines, and every fixture's start comes from the competition's own page.

| Sport | Start (UTC) | Match | Selection (the pick) | Our price | US | Sources |
|---|---|---|---|---|---|---|
| Rugby Union | Sat 24 Oct 18:45 | Ospreys v Dragons (URC R4) | Ospreys, To Win | 1.62 | −161 | unitedrugby.com fixtures + table |
| Ice Hockey | Sat 24 Oct 23:00 | BUF Sabres @ WAS Capitals | WAS Capitals, Money Line | 1.62 | −161 | api-web.nhle.com schedule + standings |
| Ice Hockey | Sat 24 Oct 23:00 | NSH Predators @ PIT Penguins | PIT Penguins, Money Line | 1.58 | −172 | api-web.nhle.com schedule + standings |
| Ice Hockey | Sat 24 Oct 23:00 | NY Rangers @ OTT Senators | OTT Senators, Money Line | 1.65 | −154 | api-web.nhle.com schedule + standings |
| Ice Hockey | Sat 24 Oct 23:00 | SJ Sharks @ BOS Bruins | BOS Bruins, Money Line | 1.51 | −196 | api-web.nhle.com schedule + standings |
| Ice Hockey | Sat 24 Oct 23:00 | VGS Golden Knights @ CLB Blue Jackets | VGS Golden Knights, Money Line | 1.53 | −189 | api-web.nhle.com schedule + standings |
| Basketball | Sat 24 Oct 23:30 | BKN Nets @ CLE Cavaliers | CLE Cavaliers, Money Line | 1.57 | −175 | nba.com schedule (ET clock) + standings |
| Basketball | Sat 24 Oct 23:30 | MIL Bucks @ PHI 76ers | PHI 76ers, Money Line | 1.57 | −175 | nba.com schedule (ET clock) + standings |
| Baseball | Sun 25 Oct 00:00 | TB Rays @ MIL Brewers (WS Game 2) | MIL Brewers, Money Line | 1.62 | −161 | statsapi.mlb.com schedule, Game 1 box, standings, player lines |
| Gaelic Football | Sun 25 Oct 16:00 | St Finbarrs v Nemo Rangers | St Finbarrs, Handicap | 1.62 | −161 | gaacork.ie |
| Volleyball | Sun 25 Oct 17:00 | Perugia v Pordenone | Sir Susa Scai Perugia | 1.58 | −172 | SuperLega calendar |
| Volleyball | Sun 25 Oct 17:00 | Civitanova v Padova | Cucine Lube Civitanova | 1.44 | −227 | SuperLega calendar |
| Volleyball | Sun 25 Oct 17:00 | Monza v Verona | Vero Volley Monza | 1.61 | −164 | SuperLega calendar |
| Motor Racing | Sun 25 Oct 20:00 | United States Grand Prix | Max Verstappen, outright | 3.48 | +248 | formula1.com |
| Handball | Wed 28 Oct 17:45 | HC Vardar v MT Melsungen | MT Melsungen | 1.54 | −185 | eurohandball.com |
| Handball | Wed 28 Oct 17:45 | Wisla Plock v Nantes | Orlen Wisla Plock | 1.64 | −156 | eurohandball.com |
| Handball | Wed 28 Oct 19:45 | PSG Handball v Aalborg | Aalborg Handbold | 1.71 | −141 | eurohandball.com |
| Handball | Thu 29 Oct 17:45 | GOG v Sporting CP | Sporting CP | 1.65 | −154 | eurohandball.com |
| Handball | Thu 29 Oct 19:45 | Montpellier v Dinamo Bucuresti | Dinamo Bucuresti | 1.70 | −143 | eurohandball.com |

Every row also carries our own handicap/spread and match total: on the `/olbg/` track 371 fixtures
are priced, 231 with a handicap and 115 with a total. The summary states the market the HIGH
selection is in, and the write-up names the total where it was part of the reasoning.

### What is still short, and why

Tennis, Cricket, Snooker, Darts, Golf, Rugby League and Greyhounds carry **no** released pick this
build. That is not effort — it is the release gate. Each of those sports has fixtures in the
capture (18 Cricket, 13 Tennis, 9 Darts, 1 Snooker, 83 Greyhounds rows sit at `unverified_start`),
but none has an official page in this repository's reviewed clock sources that states the start
with a time zone. Converting OLBG's own clock would be an inference, and this project does not
publish inferred starts. `FL-204` records the specific blocker per sport; the per-sport table on
`summary.html` prints the hold reason next to the next priced fixture, so the gap is visible
rather than silent.

## Verified against official sources this session

* **NBA** — `nba.com/schedule?date=2026-10-24`: eight games, tip times in ET, venues and game ids
  (BKN@CLE 7:30 PM ET Rocket Arena 0022600105; MIL@PHI 7:30 PM ET Xfinity Mobile Arena 0022600106).
  `nba.com/standings`: PHI 2-0, MIL 0-2, CLE 0-1, BKN 0-1. Both promoted rows re-price at 1.57
  (−175).
* **NHL** — `api-web.nhle.com/v1/schedule/2026-10-24` and `/v1/standings/2026-10-24`: six 23:00Z
  games; BOS 8-2-1, WSH 5-4-0 (4-2-0 home), PIT 4-6-1 (3-1-0 home), OTT 7-4-0 (4-2-0 home),
  VGK 8-4-0, plus the road splits the write-ups quote (BUF 1-1-2, NYR 1-4-1 away).
* **MLB** — `statsapi.mlb.com`: World Series Game 2 is `gamePk 849802`, `gameDate
  2026-10-25T00:00:00Z`, American Family Field, Henderson (MIL) v Rasmussen (TB); Game 1 final
  Brewers 3 – Rays 2 (`gamePk 849805`); Milwaukee 103-59 with 832 runs scored and 618 allowed,
  55-26 at home, last ten 8-2; Tampa Bay 98-64, 43-38 away. Starter lines: Henderson 2.47 ERA,
  110 K in 98.1 IP, 0.84 WHIP; Rasmussen 2.67 ERA, 0.91 WHIP.
* **URC** — the Round 4 fixture list still prints Ospreys v Dragons at St. Helen's, KO 19:45
  IRE & UK (18:45Z), Round 3 Dragons 38-31 Ospreys on 9 October.
* **OLBG** — the 17:11Z capture (18/18 listings HTTP 200, 218 tip cards) was parsed into 197 rows
  across 14 sports.

## Irregularities raised

`FL-199` (ten unit tests pinned the build clock, so an ordinary publish cycle turned the suite red),
`FL-200` (a session-prefixed capture directory sorted *below* the previous day's board, so the
fresh capture was silently ignored — the resolver now orders on the stamp, not the name),
`FL-201` (OLBG re-listed cricket 188845 as `Win Match`, so the FL-196 regression can no longer be
exercised on the live row), `FL-202` (no official injury report was retrievable for the five new
NHL fixtures, so none is claimed), `FL-203` (two of the five NHL picks name the side opposite
OLBG's crowd, from the clubs' own home/road splits), `FL-204` (the five-per-sport target is still
unmet for seven sports, with the mechanical blocker named per sport).

## Checks run on the committed tree

```
scripts/check_board.py            PASS
scripts/check_exec_summary.py     PASS  19 picks agree with data/lines.json and both prediction files
tools/check_site.py               All checks passed
scripts/check.py                  PASS  53 fixture rows
scripts/check_links.py            110 pages, 2 586 local links, 0 broken
python -m unittest discover -s tests   316 tests, OK (25 skipped)
```
