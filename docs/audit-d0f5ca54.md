# Session audit — `session-d0f5ca54` (`task-46-daily-refresh-20261023`)

2026-10-23 daily refresh against `main=46d8716`. Publication clock `2026-10-23T16:50:00Z`
(the newest `checked_at` in `data/release_checks.json`); run `S-20261023-A`.

## What was done

1. **Harvest.** One pass over all 15 allowed OLBG sport pages (chunks 0–1 only) →
   `data/raw/olbg-harvest-20261023T1630Z.tsv` (180 rows, 0 excluded-sport rows), chained
   ahead of `olbg-harvest-20261022T2130Z.tsv`. Golf returned the literal text
   “No tips found.” (**FL-131**), so golf publishes an empty board today.
   `data/matches.json` rebuilt to 432 rows (was 338).
2. **Clock discipline.** A sandbox `date -u` check mid-pass showed the real time was
   ~16:34Z, not the ~18:00Z the session had been assuming. Every re-observation in this
   pass is stamped `2026-10-23T16:50:00Z` (the reads spanned ~16:25–16:50Z); nothing is
   backdated and no certification outlives its 24-hour window.
3. **Release re-observations (24 records added/refreshed/corrected).** NHL API
   (`199984` MTL@CHI 00:00Z, `199985` TBL@COL 01:00Z on 24 Oct); NBA.com (12 Friday
   games, ET); URC fixtures-in-full Round 4 (5 records + new Cardiff `609575`);
   EuroLeague Round 7 game centre (`535925/535926/535928`); MLB.com World Series
   Game 1 (`160789`, 20:00 ET, starters Nick Martinez vs Jacob Misiorowski now named);
   formula1.com corroboration of the payload-certified `913` start (25 Oct 20:00Z);
   VolleyballWorld SuperLega #30003 (`36994`, 25 Oct 16:00Z); gaacork.ie Premier SFC
   final (`3530`, 16:00 Europe/Dublin via the page’s own calendar link).
4. **Corrections to committed evidence** (all on Flagged for Review):
   - **FL-132** — `609580` (Stormers v Scarlets) had been certified 15:00 **UTC** from a
     club page that prints no zone; the URC list says `KO 15.00 IRE & UK` = 14:00Z. Record replaced.
   - **FL-134** — five Pro D2 records quoted kick-offs as “… CET”, a token `prod2.lnr.fr`
     does not print (it shows bare `19h30`/`21h00`; France is on CEST in October anyway).
     Downgraded to `date_only`; RGU-02/03/09 honestly leave the live HIGH set.
   - **FL-135** — SuperLega verification fields mixed up between Sunday fixtures
     (`36994` venue/local clock; `36997` venue blanked).
   - **FL-136** — tonight’s EuroLeague games close **Round 7**, not Round 8 as two
     verification records and four pieces said; stale club records in `535928` withdrawn.
   - **FL-138** — Spurs venue conflict (Frost Bank Center vs Moody Center) between two
     committed records; venue blanked rather than guessed.
   - **FL-140** — 68 published piece fields contained the brief-banned words “model” /
     “verified”; reworded in place, regression-tested.
   - **FL-129 resolved** — the EuroLeague article URL serves a fresh edition today; all
     three Friday clocks re-observed verbatim from it.
5. **Root board.** 23 new curated rows (`IHO-30/31`, `BKB-33..41`, `RGU-19`,
   `TEN-49..53`, `SNK-15/16`, `DRT-19..22`, `CRK-19..21`) + 73 listing syncs from today’s
   capture. 16 rows carry governing-body fixture confirmations read this pass (NHL API,
   NBA.com, URC, WTA OP PDFs); the other 10 publish unverified (**FL-139**, test-pinned
   exemption set extended). New pieces: `IHO-30` (Montréal 1.55) and `IHO-31` (Colorado
   1.72) live HIGH; `TEN-50`/`TEN-52` analysis. `BKB-29`/`BKB-30` rewritten, `BSB-01`
   refreshed with the named starters. `www.unitedrugby.com` added to
   `source_tiers.official` (the URC’s own domain; its `stats.` subdomain and its
   release-clock trust already existed), which also made RGU-19(Cardiff v Sharks,
   MEDIUM) a verified row; `Cardiff`/`Sharks` name aliases added.
6. **NHL dating decision (FL-137).** A full 32-club `NHL_standings_2026_10_23` block was
   transcribed, but `scripts/model.py` deliberately keeps pricing from the 2026-10-22
   block: the new block already contains 22 October results and silently repriced five
   settled fixtures whose pieces quote the old prices (IHO-16 1.68→1.50). The blocks are
   gp/gf/ga-identical for tonight’s four clubs, so tonight’s prices are unaffected.
   Durable fix for a future session: per-fixture standings dating.
7. **`/olbg/` track.** 16 new/refreshed verifications (NHL ×2, NBA ×12, Cardiff, WTA SFs ×4)
   + the FL-135/136/138 corrections; `tools/build_dataset.py` → `originate.py` →
   `build_site.py` → `check_site.py` green. Pieces refreshed: `BKB-534841` (rewritten:
   Game 1 leaders, no venue), `BKB-534842`, `BKB-535925/26` (Round 7), `BSB-160789`
   (starters), `GFA-3530`; `VOL-37002` re-quoted to its moved price (1.57).

## Board state at the 16:50Z clock

- Root: **321 rows** (273 fixtures + 48 outright/race), 262 verified, 286 priced,
  **82 written pieces**. `/olbg/`: **432 rows/lines**, 94 pieces. Register: **132 items**
  (FL-131…FL-140 new this pass, FL-129 resolved).
- **Live HIGH: 12 root / 14 `/olbg/` / 18 union.** Two sports meet the five-per-sport
  target: **Basketball 5** (EuroLeague trio + Spurs, Celtics) and **Rugby Union 5**
  (URC Round 4). Ice Hockey 2, Volleyball 3, Baseball 1, Gaelic Football 1, Motor
  Racing 1. Shortfall to the 75-pick ideal: 57 — see `data/brief_coverage.json` for the
  per-sport blocker accounting.

## Why the target is still short (honest accounting)

- **Certified-clock supply is the binding constraint**, not pricing: at 16:50Z most of
  tonight’s European slate (SHL, Liiga, ICEHL, handball leagues, SuperLega undercards)
  has no governing-body page with an explicit timezone read inside 24h. The WTA Saturday
  order-of-play PDFs print no zone (TEN-49..52 stay analysis despite verified pairings);
  WST prints bare clocks; the PDC site returns only its consent manager — nine chunks of
  `/WCFAQ` included (**FL-133**), which also strands the Littler outright (DRT-18) at
  MEDIUM; `icc-cricket.com/fixtures` and `nzc.nz` fixture pages 404, so NZ v India
  (CRK-17) keeps yesterday’s pair-only confirmation.
- **Thin samples were not dressed up.** Seven of today’s nine new NBA rows price off ≤5
  community tips or non-winner markets; one (Raptors, 1.61) could technically have been
  flipped HIGH by authoring a piece, but no official form line beyond the fixture itself
  was read for it, so it stays LOW. Root basketball still has no NBA form table, so the
  two released NBA picks live on the `/olbg/` track where yesterday’s pieces back them.
- **Golf** had no listings at all (FL-131) and **Rugby League** outrights only.

## Process notes

- The COORDINATION claim text was written at session start but its commit only landed
  with the data checkpoint (`ae58fbc`). No other session was active (pre-claim fetch
  showed only `origin/main`, no open PRs), and no sibling work was touched.
- Two parallel `edit_file` calls against the same test file raced and one edit was lost;
  detected via `git diff` and re-applied deterministically. Net effect: none.
- Checks: `116/116` unit tests OK (7 new pins in `tests/test_audit_d0f5ca54.py`; 8
  date-sensitive pins rolled with dated comments), `check_board.py` PASS,
  `tools/check_site.py` PASS, `check.py` PASS, `check_links.py` 110 pages / 2,374
  links / 0 broken.

## Sources read this pass (governing bodies only)

NHL schedule API + NHL.com standings (api-web.nhle.com / nhl.com) · NBA.com games ·
EuroLeague standings + Round 7 game centre (euroleaguebasketball.net) · URC 2026/27
fixtures in full (unitedrugby.com) · MLB.com World Series schedule + Game 1 preview ·
formula1.com United States GP page · Volleyball World SuperLega #30003 · gaacork.ie
final page + league 215999 results matrix (the GAF-01 aggregates — 116–85 vs 98–79 —
recompute exactly from it) · WTA order-of-play PDFs 405/2092 · LNR Pro D2 calendar ·
WST matches page. Dead ends recorded, not retried: pdc.tv (consent wall),
icc-cricket.com/fixtures (404), nzc.nz fixtures (404), wst.tv tournament path (404).
