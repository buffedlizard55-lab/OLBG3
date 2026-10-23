# Daily cycle audit — `session-beb7787b`, 2026-10-23 16:05Z–17:50Z

Task `task-46-daily-harvest-reverify-predict-integrate-20261023`, branch `arena/beb7787b-olbg3`,
branched from `main` @ `46d8716`. No sibling session was active (open PR list empty at claim time).

## What was done

1. **Fresh OLBG harvest (16:16Z–16:40Z)** — all 15 in-scope sport listing pages (Golf via
   `/Golf/All_Golf/5`, NHL subpage included) by agent page-retrieval. 180 rows recorded verbatim in
   `data/raw/olbg-harvest-20261023T1630Z.tsv` (copy `docs/harvest-20261023-1630z.tsv`). Excluded
   sports: 0 rows. Golf and Rugby League listed outrights only; Greyhounds 36 UK race rows.
2. **Diff & ingestion** — 94 event ids new to `data/matches.json`; 64 new two-sided fixtures
   added to the root board (TEN-49..57, BKB-33..43, IHO-30..42, CRK-19..24, DRT-21..24,
   SNK-15/16, RGU-19..23, HBL-39..43, VOL-36..44). 66 existing root rows had moved OLBG
   consensus (tips/pct/pick/market synced). Start labels were re-written only where the
   resolved date or the clock text changed; the previous label is kept in `start_prev`
   (GAF-02, HBL-25, VOL-23/24/25). `tools/build_dataset.py` now recognises `Total Games`.
   Root board: 359 rows (311 fixtures + 48 outright/race), 270 verified, 310 priced.
3. **Official re-observation (pages read this session, times UTC)**
   - 16:55 NHL API schedule `2026-10-23`: MTL@CHI `startTimeUTC 2026-10-24T00:00:00Z`,
     TB@COL `01:00:00Z`; standings `2026-10-23` transcribed as `NHL_standings_2026_10_23`.
     `scripts/model.py` now chooses the newest NHL table dated on or before the fixture date,
     so 22 Oct rows keep the table they were published from (prices unchanged).
   - 17:02 URC “2026-27 fixtures in full”: Round 4 Fri/Sat clocks in `IRE & UK`
     (609575/609577/609579 19.45; 609576 12.45; 609580 15.00; 609578 18.00).
     **Correction:** the 22 Oct entry for Stormers v Scarlets had recorded 15:00 as UTC;
     it is 15:00 Irish time = 14:00 UTC (FL-133).
   - 17:04 NBA.com schedule 2026-10-23: 12 games, ET; HOU@SAS venue now Moody Center, Austin (FL-139).
   - 17:05 MLB.com playoff schedule: Game 1 Rays @ Brewers 8 p.m. ET.
   - 17:07 EuroLeague “Game Center: Round 7” article: 19:00 / 20:15 / 20:45 **CEST** clocks
     plus form notes (the game-center listing renders clocks in the reader's zone; not used).
   - 17:11 LNR Top 14 J7: 16h35 / 21h05 printed without a zone → recorded date-only (FL-134,
     consistent with FL-096). The 22 Oct Pro D2 entries labelled “CET” on a CEST date are held.
   - 17:13 WST Matches: QFs Fri 23 Oct (Jones v Donaldson M60, Gilbert v Williams M59), date-only;
     completed QFs McGill 1-6 Wilson, Craigie 6-2 Slessor.
   - 17:17/17:18 WTA order-of-play PDFs (Osaka 405, Ningbo 2092): Saturday semi-finals
     confirmed; clocks un-zoned → date-only / not-before (FL-097 precedent).
   - 17:20 Cork GAA county-final page: Sun 25 Oct 4.00pm, Páirc Uí Chaoimh (calendar link
     `ctz=Europe/Dublin`); road-to-final scorelines.
   - 17:21 Maigh Cuilinn club site: Galway final **moved to Sunday 25 Oct 4pm** (weather warning) —
     matches OLBG's new `25 Oct 12:00` label (FL-136).
   - 17:22 PREM Rugby fixtures Round 4: four pairs/dates confirmed, clocks viewer-zone → date-only.
   - FAILED: pdc.tv schedule pages returned only consent-wall text (FL-131); ICC fixtures page is
     JS-rendered; nzc.nz gives squad news but no clock.
4. **Release checks** — `data/release_checks.json` now 137 events, publication clock
   `2026-10-23T17:22Z`. New exact clocks: URC ×6 (Irish time), NBA ×12 (ET), MLB, EuroLeague ×3
   (CEST), NHL ×2 (UTC), Cork GAA (Irish time). Date-only/not-before: LNR ×3, WST ×2, PREM ×4,
   WTA ×4, Moycullen. Holds: 609561/609562.
5. **Picks & prose** — 8 live HIGH picks: BSB-01 Brewers, BKB-29 Olympiacos, BKB-30 Valencia,
   GAF-01 St Finbarrs, RGU-14 Leinster, VOL-27/28/29 (SuperLega). BKB-29/BKB-30 rewritten
   from the Round 7 article (the old text said “Round 8”, FL-137); BSB-01, GAF-01, CRK-17
   extended with today's reads. New analysis pieces: IHO-30, IHO-31, TEN-56, RGU-17, GAF-02,
   DRT-24. 24 older pieces were reworded to drop the words “model”/“verified” (FL-138); a
   regression test now scans the file.
6. **Flag register** — FL-131..FL-139 added (see `data/flagged.json`).
7. **Tests** — `tests/test_audit_beb7787b.py` (9 tests) added; six earlier audit tests relaxed
   only where they pinned a clock-dependent state (archived 22 Oct rows, harvest head, tip counts).
   118 tests pass.

## Why only 8 HIGH picks

The HIGH gate needs an official fixture, an official form table, ≥55% on our numbers, a price
inside −250..+10000 **and** a zone-labelled official clock under 24 h old. Today's shortfalls:
Edinburgh/Bulls/Stormers/Toulouse/Montreal price shorter than −250; Top 14, WTA, WST, PREM and
Pro D2 clocks are not zone-labelled; PDC pages were unreadable; NBA/European hockey/handball/
volleyball rows have no official table in the dataset (consensus-only). Nothing was inferred to
close the gap — see FL-102 (standing) and FL-132.

## Pipeline run (all PASS)

`scripts/build.py` → `build_gap_sports.py` → `model.py` → `tools/build_dataset.py` →
`tools/originate.py` → `scripts/brief_coverage.py` → `scripts/build_site.py` → `check_board.py` →
`tools/build_site.py` → `tools/check_site.py` → `scripts/build_site.py --snapshot` → `check.py` →
`check_links.py` (110 pages, 2350 links, 0 broken) → `python -m unittest discover -s tests` (118 OK).
