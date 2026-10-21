# Method

This document describes what the board actually does, as of the 2026-10-21 evening pass. Every number here is
reproducible by running the scripts named in section 7.

## 1. Scope

Included (15 sports, 137 rows): Tennis 14, Basketball 14, Ice Hockey 7, Cricket 9, Baseball 1, Volleyball 15,
Darts 14, Snooker 6, Rugby Union 15, Rugby League 3, Handball 15, Gaelic Football 5, Golf 10, Motor Racing 3,
Greyhounds 6.

Excluded as instructed: soccer/football, American football, boxing, UFC/MMA, hurling, horse racing, cycling,
specials. Gaelic football, greyhound racing and motor racing are **not** on that list, so they are included; each
carries the ambiguity on the Flagged for Review page.

Of the 137 rows, 114 are two-sided fixtures and 23 are outright or race markets (one selection, no opposing side).

## 2. Capture

Each OLBG sport listing was read and transcribed row by row into `data/sports/<sport>.json` (fixtures) and
`data/raw/gap_sports_capture_20261021.json` (outright/race markets), keeping OLBG's own strings — start label,
market, most-tipped selection, tip count, percentage — plus the event URL and event id. Nothing is normalised
except team-name aliases, which are published in `ALIASES` in `scripts/model.py` (name normalisation only, no value
changed).

## 3. Verify — and the source tier that decides the label

A row counts as **verified** only when the specific fixture appears on:

* the competition's own site (governing body, league or tour), e.g. `nba.com`, `nhl.com`, `mlb.com`,
  `atptour.com`, `wst.tv`, `cricket.co.za`, `stats.unitedrugby.com`, `prod2.lnr.fr`, `top14.lnr.fr`,
  `ice.hockey`, `euroleaguebasketball.net`, `eurohandball.com`, `ticker.ehf.eu`, `pdc.tv`, `formula1.com`; **or**
* one of the two clubs' own sites (`hapoelbc.com`, `hcb.net`, `kac.at`) — tier `club-official`.

A reputable third party (ESPN, ESPNcricinfo, Sofascore, AS, TNT Sports, ORF, snooker.org, Eliteprospects,
tipsterio.de) is recorded as **corroborated**: the link and label stay, the tier is shown in the row, the row earns
**no** verification point, and it is listed on Flagged for Review. If nothing is found, the row is **unverified**
and its official fields stay blank — never inferred.

The tier register lives in `data/official.json` → `source_tiers`, and `scripts/check_board.py` fails the build if a
row's status disagrees with its tier (an official host may not be labelled corroborated, a third-party host may not
be labelled verified, and a corroborated row may not be graded HIGH).

Current state: **105 verified** (98 official + 6 club-official + 1 outright row), **9 corroborated**,
**23 unverified** (22 outright/race marker positions and CRK-05).

## 4. Originate lines — `scripts/model.py`, `scripts/build_gap_sports.py`

Every price is ours. There are no bookmaker quotes anywhere in the repository.

| Market | Rule |
|---|---|
| Win — rugby union (URC, Pro D2, Top 14) | exp = mean(own points-for/G, opponent points-against/G); home +3.0 pts; margin = difference; sd 13 pts; win/draw/loss from the normal CDF with a ±0.5 draw band. |
| Win — ice hockey (NHL, ICEHL, SHL) | exp goals per side from official GF/G and GA/G; home +0.15 goals; P(home) = logistic(1.0 × goal difference). |
| Win — everything else | Probability = the OLBG consensus tip share, capped to [2%, 98%] because 0% and 100% cannot be priced. No draw is priced. |
| Handicap — official form | Line = projected margin forced to a half-point, quoted 1.91 each side. |
| Handicap — no official table | margin = σ × z(p), with σ per sport: Tennis 4.5 games, Basketball 13.0 points, Handball 7.0 goals, Baseball 3.0 runs, Volleyball 1.6 sets, Snooker 1.4 frames. p is capped at 0.85 so a three-tip sample cannot set an extreme line. Labelled `consensus-scaled`. |
| Handicap — cricket, darts, Gaelic football | **Not quoted.** OLBG states no format for cricket or darts (a runs line differs by an order of magnitude between T20 and a Test; a legs line needs the leg format) and no official scoring record was retrieved for the club Gaelic fixtures. |
| Total | **Only** where an official scoring baseline exists (rugby union points, ice-hockey goals). Line = projected combined score floored to the next half point, 1.91 each side. Everywhere else the cell is empty and the reason is on the page. |
| Outright / race | `p = (wins + a) / (total + k)` with a Beta(a, b) prior whose mean is 1/N (N = field size) and strength k; `odds = 0.95 / p`. N and k are disclosed per row. |
| Overround | 5% total, allocated proportionally. |

**Disclosed assumptions** (chosen constants, not measured facts): rugby home advantage +3.0 points and margin
sd 13.0; NHL/ICEHL/SHL home advantage +0.15 goals and logistic slope 1.0; the per-sport handicap scales in the
table above; the outright field sizes and prior strength. All are printed on the site's method page.

## 5. Pick and grade

Pick = the highest model probability. Confidence is a 3-factor score:

| Factor | Points |
|---|---|
| Fixture verified against an official source (tier official or club-official) | +2 |
| Official current-form data for **both** sides | +2 |
| Model probability of the pick ≥ 65% | +2 (or +1 if ≥ 55%) |

HIGH ≥ 6 · MEDIUM 3–5 · LOW ≤ 2. A row whose only input is a public tip share therefore cannot reach HIGH, and a
row that loses its official source can drop a grade — which is what happened to IHO-01 and IHO-03 in the
source-tier audit.

Current split: HIGH 12 · MEDIUM 48 · LOW 54 (114 fixtures), plus the 23 outright rows graded on their own basis.

## 6. Predictions

Written only for HIGH picks. Each is at least 30 words, names the selection unambiguously (money line, handicap or
total), gives the team or player, current form and recent results, and links the official source for every factual
claim. Twelve predictions are currently counted as high-confidence. Two more (IHO-01, IHO-03) are published
separately under "kept after the source-tier audit": their fixtures lost official status, so they are no longer
counted, but the prose is not hidden.

## 7. Build and check

```bash
python3 scripts/model.py            # data/events.json
python3 scripts/build.py            # official-feed pages
python3 scripts/build_gap_sports.py # data/gap_sports.json
python3 scripts/build_site.py       # site/
python3 scripts/build_site.py --snapshot  # mirror site/ to the repo root (legacy Pages publisher)
python3 scripts/check_board.py      # row invariants, tiers, prices, predictions
python3 scripts/check_links.py      # no broken local links
python3 -m unittest discover -s tests
```

`check_board.py` enforces: an OLBG source link with an event id on every row; status/tier agreement; no official
value on an unverified row; decimal prices that recompute; every HIGH row carries a 30+ word sourced prediction;
no merge-conflict markers in any data file. At the last build: 137 rows, 69 verified, 131 priced, 83 handicaps,
22 totals, 14 predictions, 30 pages, 0 broken links.
