# Fresh coverage and source audit — session-5a9926e5

Audit window: **2026-10-22 08:24–08:56 UTC**. Historical captures remain immutable; corrections belong in new captures and generated outputs. Local repair-candidate results are recorded below; CI, PR, merge, and deployment receipts are added only after they occur.

## Baseline and preservation

- Baseline: `f8471f7` (PR #73), with 228 root rows and 270 `/olbg/` rows.
- The preserved 07:25Z harvest is `data/raw/olbg-harvest-20261022T0725Z.tsv`, SHA-256 `ca6e3beb1eabca7d4ae1eea9a5782cc8f63c9a6ab4ef35124f6df8dd0680e13f`.
- `data/raw/gap_sports_capture_20261021.json` began this audit with SHA-256 `fe18d77823a27ba63a6cfd048b2b8b186c557e98d685ebbd3b63d546d44f6a56`.
- A reproducible standard-library HTML capturer was added in `scripts/fetch_live_sources.py`, with `.github/workflows/live-source-capture.yml`. Capture run [39747818455](https://github.com/buffedlizard55-lab/OLBG3/actions/runs/39747818455) was still queued at 08:37Z; no artifact has been presented as completed evidence.
- Concurrent sibling scopes were discovered after the default one-branch fetch hid them. The narrowed claim and non-overlap rules are recorded at the top of `COORDINATION.md`. In particular, `session-d3464fe4` owns the separate 08:30Z harvest; this audit does not duplicate that claim.

## Confirmed freshness defects

### Same-day and tournament starts

The `/olbg/` generator previously rejected only a previous calendar date. A same-day event could therefore remain HIGH after its start. Root generators already calculated `kickoff_started`, but `scripts/check_board.py` and the published-board test did not reject a HIGH row with that flag.

The code changes in this session:

1. derive an effective UTC start from the official organiser timestamp when available, otherwise from the documented OLBG US-Eastern display-clock rule;
2. use the row's actual capture date for `Today` / `Tomorrow`, not the legacy default capture date;
3. prevent HIGH when the event has started, and prevent HIGH for an unknown same-day clock;
4. retain written pieces as `analysis` after a downgrade and synchronise prediction statuses from regenerated confidence;
5. reject started HIGH rows in both validators and in unit tests, including a second check against the actual timestamp so a stale boolean cannot hide a started event.

The regression tests cover a started 07:00Z event at a 07:35Z snapshot, a future 08:00Z event, an unknown same-day clock, and an official tournament start overriding an outright settlement label. The published-data regression initially exposed stale generated rows; regeneration with the new clock fields fixed that failure.

### Golf: official first tee versus outright display date

Live OLBG golf listing: <https://www.olbg.com/betting-tips/Golf/5>

Official PGA pages:

- <https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/overview>
- <https://www.pgatour.com/tournaments/2026/butterfield-bermuda-championship/R2026528/tee-times>

The official pages state Port Royal Golf Course, Southampton, 22–25 October 2026. The Round 1 tee sheet explicitly states time zone **EDT** and its first groups are **6:35 AM EDT**, which is **10:35Z**. The current OLBG outright row `101904` displays `25 Oct 17:45`; that label must remain preserved as the source label, but it must not postpone tournament-start expiry. At the fixed 07:35Z snapshot the tournament had not started. A later final snapshot at or after 10:35Z must archive the HIGH selection rather than treating the outright as unstarted until 25 October.

## Volleyball: crossed event IDs and replacement fixtures

Live OLBG listing: <https://www.olbg.com/betting-tips/Volleyball/21>

### Italian SuperLega

Official calendar: <https://www.legavolley.it/calendario/?co=26> (the calendar itself links Regular Season `idCampionato=999`). Its Giornata 2 table confirms the following on 25 October 2026:

| Current OLBG ID | Current OLBG fixture / selection | Official fixture and time | Repair required |
|---|---|---|---|
| `36994` | Trentino–Cisterna; Cisterna, Win Match, 1/1 | Itas Trentino–Cisterna Volley, 17:00 CET, BTS Arena | Move the Trentino evidence from old ID `36995` to `36994`. |
| `36995` | Civitanova–Padova; Padova, Win Match, 1/1 | Cucine Lube Civitanova–Pallavolo Padova, 18:00 CET, Eurosuole Forum | Move the Lube evidence and written piece from old ID `36994` to `36995`. |
| `36996` | Monza–Verona; Monza, Win Match, 1/1 | Vero Volley Monza–Rana Verona, 18:00 CET, OpiquadArena | Move the Monza evidence and written piece from old ID `36997` to `36996`. |
| `36997` | Perugia–Pordenone; Pordenone to win 3–1, Set Score, 1/1 | Sir Susa Scai Perugia–Tinet Prata di Pordenone, 18:00 CET, Pala Barton Energy | Move the Perugia evidence and written piece from old ID `36996` to `36997`. Preserve the distinct OLBG Set Score market; an independently originated match-winner line is a separate market. |

The official Giornata 1 results in the same calendar confirm Lube's 3–0 win at Verona, Trentino's 3–0 win at Modena, Perugia's 3–2 win at Cuneo, Pordenone's 3–1 home win over Monza, Cisterna's 3–0 home win over Milan, and Padova's 0–3 home loss to Piacenza. The existing prose must travel by **fixture identity**, never by the old numeric ID.

### Brazilian Superliga Feminina

Official CBV scoreboard, standings and Round 2 list: <https://cbv.com.br/>

| Current OLBG ID | Current OLBG listing | CBV official Round 2 confirmation |
|---|---|---|
| `37000` | Paulistano/Barueri–Minas; Paulistano/Barueri to win 3–1, 1/1, Tomorrow 17:30 | **Gerdau Minas × Paulistano Barueri**, 23 Oct, 18:30 BRT. CBV order conflicts with OLBG's displayed home/away order; flag this irregularity rather than hiding it. |
| `37001` | Brasilia–Sesc RJ Flamengo; Brasilia, 2/2, Tomorrow 17:30 | Brasília Vôlei / BRB × Sesc RJ Flamengo, 23 Oct, 18:30 BRT. |
| `37002` | Mackenzie–Osasco; Mackenzie to win 3–1, 1/1, 24 Oct 15:00 | Batavo Mackenzie × Osasco São Cristóvão Saúde, 24 Oct, 16:00 BRT. |
| `37003` | Abel-Moda Brusque–Praia Clube; Abel/Moda Brusque, 1/1, 24 Oct 20:00 | Brusque Vôlei × Dentil Praia Clube, 24 Oct, 21:00 BRT. |

CBV's Round 1 results confirm: Sesc RJ 3–0 Paulistano; Sesi Bauru 3–0 Mackenzie; Brasília 0–3 Osasco; Gerdau Minas 3–2 Brusque; Dentil Praia Clube 3–0 Pinheiros; Fluminense 3–2 Sancor. The current four fixtures must receive new verification records based on these facts. They must **not** inherit the prior IDs' Brasilia/Osasco/Sesi/Paulistano records blindly. The 08:35Z correction overlay replaces all four crossed IDs. Old Osasco–Sorocaba and Sesi Bauru–Fluminense rows remain only in immutable historical input; they are not retained as current published rows.

## Other live-source drift requiring fresh-capture reconciliation

These are observations from the live listing pages, not permission to overwrite historical raw files:

- **Tennis:** <https://www.olbg.com/betting-tips/Tennis/3> — Bublik–Marozsan `902082` moved from the raw 3/4 to 4/5 (80%). Official Almaty schedule: <https://www.atptour.com/en/scores/current/almaty/9410/daily-schedule>.
- **Basketball:** <https://www.olbg.com/betting-tips/Basketball/4> — live changes include Changwon Sakers `536021` 4/8, Crvena Zvezda `535924` 2/3 and Uniao Corinthians `536020` 1/2. Official EuroLeague game centre: <https://www.euroleaguebasketball.net/en/euroleague/game-center/>.
- **Snooker:** <https://www.olbg.com/betting-tips/Snooker/8> — live selections/tip splits differ for Wilson `9940`, Baranowski `9946`, Mark Williams `9943`, Cheung Ka Wai `9945` and Daniel Wells `9941`; `9941` is now Daniel Wells Win Match 2/2 rather than the raw Jak Jones handicap row.
- **Golf:** <https://www.olbg.com/betting-tips/Golf/5> — only Bermuda `101904` and Stifel `101903` were visible in this retrieval; prior extra-event coverage cannot be described as a fresh current listing without another capture.
- **Baseball:** <https://www.olbg.com/betting-tips/Baseball/12> — only TB Rays @ MIL Brewers `160789`, Tomorrow 20:00, MIL Money Line 14/17 (82%) was visible.
- **Greyhounds:** <https://www.olbg.com/betting-tips/Greyhounds/28> — early races `689570`, `689576`, `689581`, `689584` each showed 1/1 but had already started; they must not be reintroduced as upcoming HIGH picks.
- **Rugby League:** <https://www.olbg.com/betting-tips/Rugby_League/10> — current outrights include State of Origin 2027 `2695857`, Super League 2027 `2801554`, and NRL 2027 `2801600`.
- **Motor Racing:** <https://www.olbg.com/betting-tips/Motor_Racing/14> — USA Grand Prix `913` moved to Max Verstappen 12/33 (36%).
- **Gaelic Football:** <https://www.olbg.com/betting-tips/Gaelic_Football/25> — six visible markets (`3530`, `3532`, `3531`, `3536`, `3537`, `3327`) require coverage reconciliation against the five-row gap input.

## Local repair-candidate results — 08:56 UTC

- Added immutable `data/raw/olbg-volleyball-correction-20261022T0835Z.tsv`, SHA-256 `55987f3a495cff241b1833824867988684460fc42c31aa90ee3f2e87c137d79f`. The 07:25Z and gap-source hashes above are unchanged.
- Applied the eight-row overlay by event ID while preserving first-seen historical chain order. Remapped Italian official-strength evidence and written pieces by fixture identity; published CBV's Minas/Paulistano order while preserving the OLBG slug and flagging the conflict.
- Added FL-066 through FL-069. The register now has 69 items. Bermuda uses official `2026-10-22T10:35Z` for expiry on both tracks, while source display labels remain unchanged.
- Excluded every listed non-winner market from winner-consensus fallback in both models. A final semantic audit also caught team-only `1st Set Winner` labels on `TEN-06` and `TEN-29`; market-based gating now covers those too. Twelve stale consensus-derived root prices were removed, and the two remapped Brazilian Set Score rows lost their crossed official-strength evidence and are blank/LOW on the root track.
- `/olbg/` retains only disclosed independent baselines where no official-strength model exists; it does not convert Set Score, Set Betting, first-set, handicap, or totals tip share into winner probability.
- Rebuilt in workflow order from `scripts/build.py` onward; a second exact rebuild produced no diff, confirming generated outputs are current and deterministic. Final local checks: **40/40 unit tests**; root **228 rows, 210 verified, 17 unverified, 210 priced, 172 handicaps, 99 totals, 62 written pieces, 45 HIGH**; `/olbg/` **270 rows, 35 HIGH / 89 MEDIUM / 146 LOW, 40 written pieces, 69 flags, 21 pages**; `scripts/check_board.py`, `tools/check_site.py`, and `scripts/check.py` PASS with 40 feed rows; `scripts/check_links.py` PASS with **81 pages, 1,280 local links, zero broken**; `git diff --check` PASS.
- The sandbox cannot fetch the NHL/MLB/NBA hosts used by `scripts/update.py`; the authoritative update step is therefore verified in GitHub Actions rather than represented as a successful local official-source fetch.
- At the 08:52Z remote check, `origin/main` was `98b6163` and sibling `session-d3464fe4` remained claim-only at `2570b53`; no uncompleted sibling harvest was consumed. Other live-listing drift above remains explicitly pending that separately claimed fresh-capture task.
- PR, merge, CI, and Pages receipts remain pending until their actual completion and are recorded in `COORDINATION.md`.
