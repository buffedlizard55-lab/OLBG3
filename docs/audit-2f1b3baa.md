# Audit — `session-2f1b3baa` (2026-10-24, 17:56Z–18:15Z)

Task: `task-2f1b3baa-post-refresh-clarity-audit-and-final-integration` (see COORDINATION.md claim, 17:56Z).

Purpose: independent, line-by-line re-verification of the merged 2026-10-24 board (post PR #167) against **live** official sources, plus a clarity/conformance review against the standing brief. Nothing below is taken on trust from the writing sessions' notes; each line was re-read at the source during 17:56Z–18:15Z on 2026-10-24.

## 1. Baseline gates on the merged tree (main @ `330b31e`)

| Gate | Result |
| --- | --- |
| `scripts/check_board.py` | PASS — 359 rows / 311 fixtures / 48 outright; every HIGH strictly inside −250…+10000 with a live kick-off and a written prediction; prices recompute |
| `tools/check_site.py` | PASS — 20 pages / 223 fixtures / 223 lines / 11 HIGH / 49 predictions / 200 flagged on the `/olbg/` track |
| Unit suite | 309 tests OK, 25 documented dated skips |
| `scripts/check_links.py` | PASS — 0 broken local links (root scan 54 pages / 1,120 links) |
| GitHub Pages API | `status=built` at `330b31e`, 2026-10-24T18:04:44Z, no error |

## 2. Independent live re-verification of the published HIGH picks

Each row below was re-read **live** from the cited official source during this audit, not from the committed snapshots.

### Root track (`today.html` hero table, 13 live HIGH)

| Ref / pick | Official source re-read live at 18:0xZ | Result |
| --- | --- | --- |
| `IHO-200002` CAR Hurricanes ML @ STL, 1.70 (−143), 23:00Z Enterprise Center | `api-web.nhle.com/v1/gamecenter/2026020175/landing` → CAR @ STL, Enterprise Center, `startTimeUTC 2026-10-24T23:00:00Z`, `FUT`; standings: CAR 18 pts/12 GP, 47 GF/33 GA, **road 6-1-1, leagueRoadSequence 1** ("strongest away line" ✓); STL 5-4-1, **home 3-0-1** ✓, streak W2 ✓ | CONFIRMED line by line |
| `IHO-200003` WAS Capitals ML, 1.44 (−227), 23:00Z Capital One Arena | gamecenter `2026020173` → BUF @ WSH, Capital One Arena, 23:00Z, FUT; standings: WSH 5-4-0, 30/29, **home 4-2-0** ✓; BUF 37 GA in 10 ✓, **road 1-1-2** ✓ | CONFIRMED line by line |
| `IHO-200006` PIT Penguins ML, 1.53 (−189), 23:00Z PPG Paints Arena | gamecenter `2026020172` → NSH @ PIT, PPG Paints Arena, 23:00Z, FUT; PIT 4-6-1, 37/38, home 3-1-0 ✓; NSH 3-3-3, 23 GF ✓ | CONFIRMED line by line |
| `IHO-200010` EDM Oilers (Game Totals row), 1.41 (−244), 23:00Z Rogers Place | gamecenter `2026020176` → TOR @ EDM, Rogers Place, 23:00Z, FUT; EDM 8-1-1, 47/32, +15, streak W3 ✓; TOR 6-4-2, 43/39, +4, W3 ✓ | CONFIRMED line by line |
| `IHO-200005` SEA Kraken ML, 1.70 (−143), 02:00Z 25 Oct, Climate Pledge Arena | gamecenter `2026020179` → MIN @ SEA, Climate Pledge Arena, `2026-10-25T02:00:00Z`, FUT; SEA 7-3-1, 44/37, home 3-1-0, W2 ✓; MIN 6-3-2, 32 GF, home 4-0-0 ✓ | CONFIRMED line by line |
| `BSB-160792` MIL Brewers ML, 1.67 (−149), World Series Game 2, American Family Field, 00:00Z 25 Oct | `statsapi.mlb.com` schedule → gamePk 849802, "World Series Game 2", `2026-10-25T00:00:00Z`, Scheduled, American Family Field, TB @ MIL, probables Rasmussen/Henderson, MIL leads series 1-0; standings (regularSeason, lastUpdated 2026-10-23): **MIL 103-59, 832/618** ✓; **TB 98-64, 736/650** ✓ | CONFIRMED line by line |
| `RGU-609581` Dragons to win @ Ospreys, 1.72 (−139), St Helen's, KO 19.45 IRE&UK 24 Oct (18:45Z) | `unitedrugby.com` 2026/27 fixtures-in-full page re-read live → Round 4, Saturday October 24, "Ospreys v Dragons — St. Helen's, Swansea, KO 19.45 IRE & UK" ✓ (the 45-minute OLBG listing gap stays published as FL-195) | CONFIRMED (fixture, venue, clock) |
| `GAF-01` St Finbarrs (Handicap angle), 1.62 (−161), Cork PSF final | `gaacork.ie` event page re-read live → final, Sunday 25 October, 4.00pm Europe/Dublin, SuperValu Páirc Uí Chaoimh; road to the final: St Finbarrs 2-12 to 0-16 v Clonakilty ✓, Nemo 1-15 to 0-16 v Carrigaline ✓; Google-calendar block confirms 20261025T160000 Europe/Dublin | CONFIRMED line by line |
| `MTR-01` Max Verstappen to win US GP race, 3.48 (+248) | `formula1.com/en/racing/2026/united-states` re-read live → Race **Sunday 25 Oct 16:00 track time**; circuit 5.513 km ✓, 56 laps ✓, 308.432 km ✓; FP2 table (Leclerc 1:35.291, Verstappen P3 +0.189s) matches the page's published practice narrative | CONFIRMED (fixture + circuit facts) |
| `HBL-12130` HC Vardar ML v MT Melsungen, 1.68 (−147), EHF CL Group B, Wed 28 Oct, 18:45 CET | `ehfcl.eurohandball.com` standings/calendar re-read live → fixture exists **2026-10-28, 18:45** ✓; standings: Vardar Group B **4th, 5 GP, 1-0-4, 154:158, 2 pts** ✓ — every number quoted in the write-up matches | CONFIRMED line by line |
| `VOL-27/28/29` (Perugia, Civitanova, Monza home wins) | `en.volleyballworld.com` snapshot `…-30002.txt` re-read: "Perugia-Tinet Prata di Pordenone, SuperLega 2026/27, 25.10.2026, Perugia, 18:00 local" ✓; live `legavolley.it` SuperLega calendar page re-read confirms all six clubs compete in SuperLega 2026/27 | Fixture CONFIRMED; per-match round-1 score claims anchored to the cited `legavolley.it` pages (cited on the rows) |
| (also on hero) Gaelic/others | see above | — |

### OLBG lines board (11 live HIGH)

- All five **EHF Champions League Round 6** fixtures pulled from the same live EHF standings/calendar page: Orlen Wisla Plock v HBC Nantes (28 Oct 18:45) ✓, HC Vardar 1961 v MT Melsungen (28 Oct 18:45) ✓, Paris Saint-Germain v Aalborg Håndbold (28 Oct 20:45) ✓, GOG v Sporting CP (29 Oct 18:45) ✓, Montpellier v Dinamo Bucuresti (29 Oct 20:45) ✓. Selection directions are consistent with the same page's standings (Aalborg 1st Group C 9 pts vs PSG 2nd 7 ✓; Sporting 1st Group D 9 pts vs GOG 2nd 7 ✓; Dinamo 3rd Group E 3 pts vs Montpellier 4th 2 ✓; Plock 1st Group B 6 pts vs Nantes 3rd 6 ✓).
- Volleyball (Perugia/Civitanova/Monza) and MTR-01: same checks as the root rows above.
- GAF (St Finbarrs) and RGU (Ospreys v Dragons): same checks as above.

### Conformance sweep (both tracks)

- All 24 HIGH write-ups are ≥ 30 words (min 60) and contain none of the prohibited outward words (`model`, `verified`/`verification`/`verify`); scanned programmatically.
- `data/predictions-olbg.json` states the odds-window policy explicitly: every HIGH strictly inside −250…+10000 with fair probability < 70% (so no >70% market-chalk picks are promoted) — matches the brief's band requirement; `check_board.py` re-enforces it on every build.

## 3. Irregularities found and handed for review (non-blocking per brief)

1. **Cross-track opposing picks on the same fixture.** Two events publish opposite HIGH selections on the two boards: OLBG event `12130` HC Vardar v MT Melsungen — root board picks **HC Vardar** @1.68, `/olbg/` board picks **MT Melsungen** @1.54; event `609581` Ospreys v Dragons — root board picks **Dragons** @1.72, `/olbg/` board picks **Ospreys** @1.62. The methodology page explains the boards use different methods, and each row is internally consistent (own price, own write-up, own release gate), but "the same team both winning and losing at HIGH confidence" reads as a contradiction on one executive page. Recommended resolution for a later session: when both boards cover one fixture, either agree the selection or visibly mark the pair as "boards disagree". Logged in COORDINATION.md; flagged here rather than silently edited, because harmonising picks is editorial work that belongs in a refresh pass, not an audit.
2. **Committed PDF evidence is not byte-faithful.** `data/raw/cited-20261024T1710Z/pages/ehfel-…-playing-times-pdf.txt` (303 KB) is a UTF-8 text round-trip of a binary PDF (mojibake `` bytes, broken xref). A reviewer cannot re-parse the PDF from the repo; the fixture evidence relies on the live source instead. Recommendation: store PDFs as binary artifacts (or base64) in future captures.
3. **Standing item restated:** the five-per-sport daily target sits at 17 distinct live HIGH across 15 sports (target 75; Ice Hockey and Handball meet 5/5) — published on `brief.html`/`today.html` with per-sport blockers; not padded, per the brief's no-invention rule.

## 4. What this session deliberately did NOT do

- No new OLBG capture (sibling harvests active; my scope excludes captures).
- No edit to pick content/grades/prices — audit only.
- No changes to `.github/workflows/*`.

## 5. Regression pins added

`tests/test_audit_2f1b3baa.py` — see header comment. Pins the invariants this audit confirmed so a later build cannot silently regress them: HIGH band + release gating + ≥30-word prohibition-free write-ups on both tracks; `today.html` present in the nav and rendering one row per live HIGH with an official `https` source; brief-coverage accounting recomputes.
