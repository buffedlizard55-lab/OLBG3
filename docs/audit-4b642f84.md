# Evening live refresh audit — `session-4b642f84`, 2026-10-22 20:58Z–23:15Z

Task `task-45-evening-live-refresh-reverify-predict-integrate-20261022` (renumbered at merge; task-43/44 were taken by sibling evening sessions), branch `arena/4b642f84-olbg3`.

> **Merge note (written at integration time):** this session ran in parallel with sibling
> evening sessions (`784afe97`, `c038b7f4`, `22fd95c8`, `a1e5112b`) whose PRs #100–#111 reached
> `main` (`d3ed893`) first with their own 20:55Z harvest, hold resolutions and register items
> FL-099..FL-126. This session's work was therefore re-applied on top of `d3ed893`, keeping only
> net-new contributions: the 21:30Z harvest as the newest chained capture, the 30 new root
> fixtures (siblings had added their evening events to `/olbg/` only — their FL-126), nine
> governing-body fixture confirmations, the 22:10Z release re-observations (NHL ×4, MLB,
> SuperLega ×3), five new root pieces, and two register items renumbered **FL-127/FL-128**.
> Overlapping items were dropped in favour of the siblings' versions: the DRT-17 tie handling
> (their FL-107/FL-124 went further and withdrew the selection), the five-per-sport shortfall
> (their FL-102), and the SSR-truncation note (covered by their FL-100/FL-120/FL-123/FL-126).
> Tip-count merge rule: totals only grow, so the larger (fresher) read wins — in the event only
> 2 of this session's 21:30Z syncs beat the siblings' later reads. Sections below describe the
> session's own pass as performed against the 12:40Z snapshot; counts in §2/§7/§8 refer to that
> pre-merge state and are superseded where this note says so.

## What was done

1. **Fresh OLBG harvest (21:00Z–21:35Z)** — all 15 in-scope sport listing pages plus the
   NHL subpage and the Darts European Championship event page, by agent page-retrieval.
   118 rows recorded verbatim in `data/raw/olbg-harvest-20261022T2130Z.tsv` (copy in
   `docs/harvest-20261022-2130z.tsv`). Excluded sports: 0 rows (soccer/football, american
   football, boxing, UFC, MMA, hurling, horse racing, cycling, specials untouched).
   Snooker/8 and Greyhounds/28 returned “No tips found.”; Golf/5 showed one tournament.
   Listings are tips-sorted and “Load More Tips”-truncated — see FL-100.
2. **Diff & ingestion** — 30 events new to both tracks added as root rows
   (TEN-41..48, CRK-17/18, BKB-31/32, RGU-17/18, HBL-32..38, VOL-31..35, IHO-26..29);
   68 existing root rows had moved OLBG consensus (tips/pct/pick/market synced to the
   21:30Z read, start labels untouched); `/olbg/` grew 298 → 328 chained rows.
   Root board: 295 rows (247 fixtures + 48 outright/race), 246 verified, 265 priced.
3. **Official re-verification (governing-body pages read this session)**
   - NHL API `api-web.nhle.com/v1/schedule/2026-10-22`: tonight’s 12 games, exact
     `startTimeUTC`; fresh 22:10Z release observations recorded for the four games whose
     JSON text was read in full (2026020154–2026020157). The other eight keep their
     12:10Z observations (still under 24 h at puck drop).
   - MLB.com World Series schedule: Game 1 (Rays @ Brewers, Fri Oct 23, 8 p.m. ET)
     re-read; BSB-01 release check refreshed. MLB.com’s Game 1 feature names Jacob
     Misiorowski (fastest average fastball velocity for a 2026 starter, 100.6 mph) and
     Junior Caminero (fastest average bat speed, 79.4 mph) — added to the BSB-01 piece;
     Tampa Bay’s starter remains unnamed in the sources read and is not assumed.
   - VolleyballWorld SuperLega schedule page (#30002): 25 Oct fixtures re-read at
     17:00 UTC (Perugia/Pordenone, Civitanova/Padova, Monza/Verona) — note 25 Oct is the
     European DST changeover, so 18:00 local = 17:00 UTC; VOL-27/28/29 checks refreshed.
   - WTA official Orders of Play (PDF): Ningbo 2092 (Bejlek/Bouzkova, Fernandez/
     Alexandrova, Jovic/Diana Shnaider, Rybakina/Kawa) and Osaka 405 (Li/Tagger, Gibson/Krueger,
     Stoiana/Siniakova, Boulter/Ruzic), Friday 23 Oct. Neither PDF prints a timezone, so the
     new rows carry date-only/not-before/followed-by release records — fixture-verified,
     never clock-certified (same rule as FL-097).
   - ATP official Daily Schedules: Almaty 9410 Day 7, Lyon 496 Day 6, Brussels 7485 Day 7
     — six new quarter-final rows fixture-verified (TEN-45..48 + existing TEN-35/36).
   - ICC match pages: Afghanistan v Zimbabwe (#274659, “ODI Tri-Series in UAE, 2026”)
     still listed UPCOMING; New Zealand v India (#271647, “IND in NZ, 5 T20Is, 2026”)
     verified as a fixture. The ICC pages rendered only viewer-local clocks tonight, so
     no new timezone-qualified start was certified and CRK-10’s 09:10Z observation was
     left untouched (it ages out 09:10Z tomorrow by design).
   - EuroLeague: the cited Round 7 article and /calendar/ now return the site’s 404
     page (FL-101); the standings page loads and was re-read (PAO 6-1 +96, Fenerbahce
     5-1, Olympiacos 5-1 after tonight’s games). BKB-22’s check was NOT re-dated without
     an equivalent reading.
   - Formula1.com US GP page re-read (Race 25 Oct 16:00 in the rendered schedule with an
     ambiguous My-time/Track-time toggle): the existing source-conflict hold on 913 stands.
   - pdc.tv article bodies remained behind the consent wall in this retrieval, so no new
     PDC clock observations were recorded (existing session-kind entries stand).
4. **Consensus-flip repairs to written pieces** — tip counts quoted in prose were
   updated to tonight’s reads (IHO-15 5/9, IHO-17 5/7, IHO-23 5/8, IHO-24 4/7, IHO-14
   market-change wording, DRT-11 5/9, DRT-18 23/37 (62%), HBL-28 3/4, RGL-03 1/2).
5. **DRT-17 / DAR-32338** (superseded at merge by sibling FL-107/FL-124): outright tips now tie Littler/Gerwyn Price/van Veen at 3/16;
   Gerwyn Price re-priced 7.19 (+619) → 8.29 (+729) via `data/live_overrides.json`; piece rewritten;
   tournament started Thursday evening, so the row is analysis on both tracks.
6. **New written pieces (5)** — TEN-47 Taylor Fritz (1.44), TEN-42 Jovic (1.85, 51% — stated as a
   marginal lean), CRK-17 India (1.57), DRT-10 Ryan Joyce (1.76), DRT-09 Jonny Clayton (1.30,
   out-of-band explained). All ≥30 words, selection-first, facts from the captured
   official rankings/seedings and tonight’s official pages; all labelled analysis by the
   release gate where no exact clock exists. Total pieces: 78.
7. **Live HIGH state at the 22:10Z snapshot** — 14 on root (BSB-01, BKB-22, CRK-10,
   GAF-01, RGU-14, VOL-27/28/29, five NHL moneylines expiring at 23:00Z–02:00Z puck
   drops, DRT-18 outright) and 12 high on `/olbg/`. Per-sport 5-a-day accounting: FL-099.
8. **Flags drafted** — 5-per-sport shortfall, SSR truncation, EuroLeague 404, 32338 tie,
   21 unverified evening rows. At merge, the first three topics were already owned by sibling
   items (FL-102, FL-100/FL-120/FL-123/FL-126, FL-107/FL-124) and were dropped; the EuroLeague
   404 and the 21 root rows landed as **FL-127** and **FL-128**. Register: 120 items.

## Verification performed

- `python3 -m unittest discover -s tests` — 76/76 OK (7 new pins in
  `tests/test_audit_4b642f84.py`; three pre-existing audit tests had their dated
  snapshot pins updated to tonight’s observed values with in-line rationale:
  VOL-37005 demotion at start, DRT-17 3/16, DAR-26023 2.34, IHO-10 expiry, tip syncs,
  and the 100%-verified invariant now exempts exactly the FL-103 set).
- `scripts/check_board.py` PASS (295 rows / 247 fixtures + 48 outright / 246 verified /
  265 priced / 78 predictions).
- `tools/check_site.py` PASS (21 pages / 328 fixtures / 328 lines / 12 high / 53
  predictions / 103 flagged after rebuild).
- `scripts/check.py` PASS (40 feed rows); `scripts/check_links.py` — 85 pages, 1,529
  local links, 0 broken.
- Two consecutive full rebuilds are byte-identical (`git diff --stat` unchanged).

## Limits (not done, deliberately)

- `scripts/update.py` and `scripts/discovery.py` were not run in the sandbox (outbound
  allowlist blocks them; running them here would only record sandbox network failures).
  CI runs both on every push and hourly; the feed track remained byte-identical.
- NHL release observations were refreshed only for the four games read in full from the
  API response chunk; no gamecentre landings were fetched tonight.
- The “(Final)” suffix on CRK-10’s stored competition name (“UAE ODI Tri-Nation Series
  2026 (Final)”) was not re-confirmed tonight — the ICC page title read was “ODI
  Tri-Series in UAE, 2026”. Left as recorded by the 09:10Z observation; noted here for
  manual review.
- No bookmaker odds were observed at any point; every price is the project’s own model
  output (0.95/p with the disclosed priors), exactly as before.
