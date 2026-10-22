# Method

This document describes the published board at the **2026-10-22T08:29:05Z snapshot**. The two dashboard tracks share evidence but use separate, documented pricing implementations. Generated JSON, not this prose, is authoritative for row-level values.

## 1. Scope and current coverage

The root board contains **228 rows: 201 two-sided fixtures plus 27 outright/race rows**, across 15 included sports:

- Tennis 37, Handball 31, Basketball 30, Volleyball 29, Darts 16, Rugby Union 15, Snooker 14, Ice Hockey 13;
- Cricket 10, Golf 10, Greyhounds 10, Gaelic Football 6, Motor Racing 3, Rugby League 3, Baseball 1.

The `/olbg/` audit track contains **270 rows** across the same 15 sports. Soccer/football, American football, boxing, UFC/MMA, hurling, horse racing, cycling and specials are excluded. Gaelic football, greyhound racing and motor racing are not named by the exclusion list and remain included with their ambiguity notes.

## 2. Capture and provenance

Historical files in `data/raw/` are not rewritten. The current merged harvest is `olbg-harvest-20261022T0829Z.tsv`: it carries the 07:25Z primary rows verbatim and re-reads OLBG event ids **101904, 101903 and 536021** at 08:29Z. It is not represented as a fresh all-sport crawl or as Load-More pagination coverage.

The root model applies `olbg-root-overlay-20261022T0829Z.json` only to explicitly named OLBG fields on matching event ids. Every overlaid row carries capture date `2026-10-22`, preventing a new “Today” label from being resolved against the previous day's date. Official names, verification and model inputs are not inferred from the overlay. Outright/race rows use the newest dated `gap_sports_capture_*.json`, with per-row capture timestamps.

Raw OLBG labels remain visible when an official source disagrees. For Mobis–Changwon, for example, the raw label resolves to 23 October while KBL officially lists 22 October at 19:00 KST; the official `2026-10-22T10:00:00Z` instant governs expiry and the conflict is flagged as `FL-068`.

## 3. Verification tiers and independent field evidence

A root fixture is **verified** only by a competition governing body/league/tour or a club-official source. A reputable third party is only **corroborated**, earns no verification points and cannot be HIGH. Missing evidence stays blank and **unverified**. The current root split is **215 verified, 0 corroborated and 13 unverified**. The `/olbg/` track separately records 216 `verified`, 7 `verified_market_row`, 2 `verified_secondary_only` and 45 `unverified` rows.

Fixture, current-form, entrant and field-size evidence are different claims:

- `field_size_status=official` requires an independent official field URL and is checked by both pipelines;
- `field_size_status=model_input` means the number is an assumption used for pricing, not an official fact;
- `competition_format` covers a known format such as two-state State of Origin without pretending an entrant count was harvested.

JGTO explicitly states **Confirmed 96 / Planned 96** for the Fortinet Players Cup, so that field is official. Bermuda 120, BMW Ladies 78 and the without-Antonelli 21-runner value remain model inputs even though their tournaments are verified. See `FL-066`.

## 4. Independent line origination

All published prices are originated here, not bookmaker quotations.

### Root track

`scripts/model.py` uses official league tables, standings, rankings and scoring data where available for rugby union, ice hockey, EuroLeague basketball, baseball, cricket, darts, tennis, handball, snooker and volleyball. Where no defensible official-form model exists, it uses a shrunk OLBG consensus input and caps confidence accordingly. Exact selection-label aliases are explicit and source-backed; fuzzy team matching is not used.

The root board currently has **224 priced rows, 186 handicap lines and 99 totals**. A blank price means no defensible input, not a value to fill by guessing. Handicaps use projected margins or disclosed sport-specific scales. Totals require a documented scoring baseline.

`scripts/build_gap_sports.py` prices outright/race markets with:

```text
a = k / N
p = (wins + a) / (total + k)
decimal price = 0.95 / p
```

`N` and `k` are published per row. The field-provenance rules in section 3 apply independently of the formula.

### `/olbg/` track

`tools/originate.py` uses Beta/Dirichlet shrinkage, disclosed home-edge logits and the separately audited `OFFICIAL_STRENGTH` inputs. It publishes match-winner, handicap/spread, totals and outright fields where supported. Current grades are **31 HIGH, 95 MEDIUM and 144 LOW**.

Both tracks use a 5% overround and standard decimal/American conversion.

## 5. HIGH band and freshness

The requested band is **-250 through +10000 American**, equivalent to **1.40 through 101.00 decimal**. On `/olbg/`, HIGH also requires fair probability strictly below 70%. On the root model, the 5% overround and 1.40 floor already prevent a pick at or above roughly 68% true probability from being HIGH.

Root confidence starts with a six-point evidence score: two points for an official fixture, two for official form and two for a model probability of at least 55%. HIGH then additionally requires an in-band price and a start that has not passed. Started HIGH candidates become MEDIUM analysis; they do not remain live recommendations with a cosmetic badge.

The committed clock is `SNAPSHOT_UTC=2026-10-22T08:29:05Z`. `OLBG_NOW_UTC=YYYY-MM-DDTHH:MMZ` reproduces another snapshot, and `OLBG_AS_OF=YYYY-MM-DD` overrides date-level expiry. At 08:29, four root and four `/olbg/` written pieces moved from HIGH to archived analysis.

## 6. Written predictions

The root board has **62 written pieces: 41 HIGH and 21 analysis**. `/olbg/` has **40: 31 HIGH and 9 analysis**. Every piece exceeds 30 words, names an explicit selection and cites sources. HIGH pieces use verified team/player, current-form and recent-history evidence. Archived analysis stays visible with its withdrawal reason.

Both checkers compare each written selection to its originated row and validate quoted prices. This prevents a refreshed line from leaving stale prose or a different selection behind.

## 7. Reproduce and verify

Run the workflow order:

```bash
python3 scripts/update.py
python3 -m unittest discover -s tests -v   # 38 tests
python3 scripts/build.py
python3 scripts/build_gap_sports.py
python3 scripts/model.py
python3 scripts/build_site.py
python3 scripts/check_board.py
python3 tools/build_dataset.py
python3 tools/originate.py
python3 tools/build_site.py
python3 tools/check_site.py
mkdir -p site/olbg && cp -r olbg-board/. site/olbg/
python3 scripts/build_site.py --snapshot
python3 scripts/check.py
python3 scripts/check_links.py
```

`check_board.py` enforces source tiers, outright arithmetic, independent field provenance, band/freshness rules, selection/price consistency and prediction length. `tools/check_site.py` additionally checks the `/olbg/` host allowlist and every generated internal link. Structural checks cannot prove that a source supports a claim; manual review links and all remaining irregularities stay on the Flagged for Review pages.
