# Audit Report — `session-b322f52e` (`task-55`, 2026-10-23T21:27Z–21:55Z)

## 1. Executive Summary

- **Session / Branch:** `session-b322f52e` (`arena/b322f52e-olbg3`), claimed as `task-54-b322f52e` against `main` `6241660` and reconciled cleanly onto `origin/main` (`8f91051`, preserving `session-a87a3681` PRs `#156`/`#158` and `session-655b300a` PR `#157`) as **`task-55`**.
- **Root Cause Found & Repaired (`FL-194`, explaining `FL-180` / `FL-185`):** Evening OLBG listing responses (`19:35Z` in `session-ebe6dc9c`, `21:33:06Z` in `data/raw/svelte-b322f52e-20261023T2133Z`, and `21:35Z` in `data/raw/live-20261023T2135Z`) return HTTP 200 with 290–350 KB HTML whose `<body>` renders `<p>No tips found.</p>` and `0` `<div class="grd tip content-visibility-auto">` cards while embedding the complete active tip table inside the SvelteKit `<script>` hydration payload with string-serialized numeric fields (`expired:"0"` instead of `expired:0`). Added an opt-in balanced-brace SvelteKit hydration parser (`--svelte-fallback`) to `scripts/extract_listings.py` — keeping default SSR extraction untouched so `olbg-harvest-20261023T1700Z.tsv` (177 rows) and `olbg-harvest-20261023T2135Z.tsv` (`FL-180` SSR-empty evidence) remain byte-identical — and extracted **123 active `expired == "0"` rows across 12 sports** into `data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv`, adding **43 net-new upcoming fixtures** to `/olbg/` (`223` total fixtures, up from `180`).
- **Four Additional Code & Data Defects Repaired (`FL-176`, `FL-195`..`FL-198`):**
  1. **`FL-176` resolved (`tools/build_site.py`):** `/olbg/index.html` High-confidence picks table now renders every source link in `p["sources"]` (`source 1 · source 2`) rather than only `sources[0]`.
  2. **`FL-195` (`RGU-609581` Ospreys v Dragons):** Caught OLBG's `startDate` (`2026-10-24T18:00:00.000Z`) running **45 minutes early** against the official URC Round 4 fixture list (`KO 19.45 IRE & UK` = `2026-10-24T18:45:00Z`).
  3. **`FL-196` (`CRI-188845` Toronto Kings vs Vancouver Guardians T20):** Added `"Top Team1 Batsman"` identically across `tools/build_dataset.py` (`OTHER_MARKETS`), `tools/originate.py` (`_non_win`), and `scripts/model.py` (`NON_WIN_CONSENSUS_MARKETS`) so `"RRS Cornwall (Toronto Kings)"` cannot leak `(Toronto Kings)` into two-way match-winner pricing.
  4. **`FL-197` (`VOL-36995` & `VOL-36996`):** Cleared swapped wrong-city arenas (`BTS Arena, Trento` on Civitanova vs Padova; `Pala Barton Energy, Perugia` on Monza vs Verona), fixed `36995`'s local start (`18:00 Local Time (CET)`), and corrected `36995`'s Round 1 rally tally from `97:85` to the official Volleyball World SuperLega table's `78:65`.
  5. **`FL-198` (`tools/originate.py` `our_home_probability` inversion):** Repaired `EDITORIAL_STRENGTH` `our_home_probability` resolution to use `resolve_team_side(pick, home, away) == home` instead of raw `pick == home`, fixing inverted home probabilities on five rows including live HIGH picks `RGU-609576` (`0.38` -> `0.62`), `RGU-609580` (`0.40` -> `0.60`), and `VOL-36997` (`0.4005` -> `0.5995`).
- **Live HIGH Coverage Expansion (Zero Inference, 100% Official Sources):**
  - Combined live HIGH union expanded to **27 picks** across **8 sports**, with **2 sports meeting the full 5-picks-per-day brief target**:
    - **Basketball:** **10 live HIGH picks** (`BKB-534842`, `BKB-534841`, `BKB-536034`..`536039`, `BKB-536042`, `BKB-536043`), maintaining `>= 5` live HIGH picks even after the `23:00Z` tip-off wave.
    - **Handball:** **5 live HIGH picks (`meets_target = True`)** across EHF Champions League Men Round 6 (`HAN-12138` Orlen Wisla Plock, `HAN-12130` MT Melsungen, `HAN-12134` Aalborg Handbold, `HAN-12129` Sporting CP, `HAN-12133` Dinamo Bucuresti), each backed by EHF's official `(CET)` playing-times PDF, 5-game group standings, and Round 5 match reports.
    - **Rugby Union:** **4 live HIGH picks** (`RGU-609576`, `RGU-609578`, `RGU-609580`, plus newly captured `RGU-609581` Ospreys v Dragons).
    - **Volleyball:** **3 live HIGH picks on both tracks** (`VOL-27`/`VOL-36997`, `VOL-28`/`VOL-36995`, `VOL-29`/`VOL-36996`).
    - **Ice Hockey:** **2 live HIGH picks on both tracks** (`IHO-199984`/`ICH-199984`, `IHO-199985`/`ICH-199985`).
    - **Motor Racing:** **1 live HIGH pick restored on both tracks** (`MTR-01`/`MTR-913` Max Verstappen `3.48 / +248`) via Formula 1's official Austin timetable (`15:00` local, `"Austin is 5 hours behind UTC"` -> `20:00Z`) and FP1 classification.
    - **Baseball:** **1 live HIGH pick on both tracks** (`BSB-01`/`BSB-160789` Milwaukee Brewers).
    - **Gaelic Football:** **1 live HIGH pick on both tracks** (`GAF-01`/`GFA-3530` St Finbarrs).

---

## 2. Official Sources Retrieved & Verified (`2026-10-23T21:30Z–21:38Z`)

1. **Runner Capture & Probes (`live-harvest.yml` run `40027576151`, commit `7c4cbc1`):**
   - `data/raw/svelte-b322f52e-20261023T2133Z/` (all 18 in-scope OLBG listing endpoints at `2026-10-23T21:33:06Z`, HTTP 200).
   - `data/raw/official-20261023T2134Z/` (`mlb_schedule.json`, `mlb_standings.json`, `nhl_schedule.json`, `nhl_standings.json`, governing-body text probes).
   - `data/raw/cited-20261023T2134Z/` (25 cited governing-body pages incl. `protennislive.com/posting/2026/9410/op.pdf`, `top14.lnr.fr`, `unitedrugby.com`, `volleyballworld.com`, `formula1.com`).
2. **Direct Governing-Body Page Reads (`fetch_page`):**
   - Formula 1: `https://www.formula1.com/en/racing/2026/united-states` & `https://www.formula1.com/en/latest/article/formula-1-msc-cruises-united-states-grand-prix-2026.2u6li2pzNhPzL3TSYaagrm`
   - Volleyball World (SuperLega): `https://en.volleyballworld.com/volleyball/competitions/superlega/standings/` & `schedule/30001/`, `30002/`, `30003/`
   - NBA: `https://www.nba.com/schedule?date=2026-10-23`, `https://www.nba.com/standings`, and game previews `0022600094`, `0022600098`, `0022600101`, `0022600102`, `0022600103`
   - United Rugby Championship: `https://www.unitedrugby.com/latest/news/2026-27-fixtures-in-full/` & `https://stats.unitedrugby.com/match-centre/table/2026-27`
   - European Handball Federation (EHF CL Men): `https://ehfcl.eurohandball.com/men/2026-27/standings/`, `https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf`, match details `OrlenWislaPlock-HBCNantes` & `FCPorto-OneVeszprémHC`, and Round 5 official reviews (`kielce-to-main-round-high-octane-veszprem-take-fuechse`, `gog-in-the-main-round-szeged-and-montpellier-out`)
   - ATP Tour / ProTennisLive: `https://www.protennislive.com/posting/2026/496/{op,mds}.pdf` (Lyon) & `https://www.protennislive.com/posting/2026/9410/{op,mds}.pdf` (Almaty)
   - Uncertified / cookie-walled sources left unverified by rule: `https://www.pdc.tv/WCFAQ` & `pdc.tv` Dortmund preview (CookieYes consent wall only; `26023` left `stale_source`), `premrugby.com` (JS filter shell), ATP Lyon/Almaty `op.pdf` (`Followed By` / `Not Before 18:00` without printed timezone; recorded `date_only` / `not_before` per `FL-097`), LNR Top 14 (`16h35` / `21h05` without printed timezone; recorded `date_only` per `FL-148`).
