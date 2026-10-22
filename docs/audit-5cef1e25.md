# Morning OLBG Re-Harvest, Official-Source Audit & Policy Repair Ledger (`session-5cef1e25`, `2026-10-22 07:25Z`)

## 1. Executive Summary

At `2026-10-22 07:24–07:35 UTC`, `session-5cef1e25` re-fetched the main `OLBG.com` hub (`https://www.olbg.com/betting-tips`) and every subpage across all **15 allowed sports** (strictly enforcing the standing ban on `soccer`, `boxing`, `ufc`, `mma`, `football`, `american football`, `hurling`, `horse racing`, `cycling`, `specials`) and cross-checked every new and previously unverified row directly against primary governing-body and official club websites.

### Headline Outcomes
1. **33 brand-new live OLBG events + 10 consensus shifts captured (`docs/harvest-20261022-0725z.tsv`):**
   - **Snooker (`+8` new Round 3 / Last 16 matches):** Full BetVictor Northern Ireland Open Last 16 slate at Waterfront Hall, Belfast (`Kyren Wilson vs Pang Junxu`, `Matthew Selt vs Sam Craigie`, `Anthony McGill vs Mateusz Baranowski`, `Elliot Slessor vs Ricky Walden`, `David Gilbert vs Cheung Ka Wai`, `Mark Williams vs Martin O'Donnell`, `Jak Jones vs Daniel Wells`, `Jordan Brown vs Scott Donaldson`), 100% verified with exact world rankings and Round 2 frame scores on `snooker.org` and `wst.tv`.
   - **Volleyball (`+8` new matches):** Full Round 2 slates across Italy's **SuperLega Credem Banca** (`Trentino vs Cisterna`, `Perugia vs Prata di Pordenone`, `Lube Civitanova vs Padova`, `Monza vs Verona` — verified with exact Round 1 set scores on `legavolley.it`) and Brazil's **Superliga Feminina** (`Brasília vs Sesc RJ Flamengo`, `Osasco vs Sorocaba`, `Sesi Bauru vs Fluminense`, `Paulistano Barueri vs Gerdau Minas` — verified on `cbv.com.br`).
   - **Basketball (`+6` new matches + `5` consensus updates):** All remaining **EuroLeague Round 7** clashes (`FC Bayern Munich vs Dubai Basketball`, `Olimpia Milano vs FC Barcelona`, `Partizan Belgrade vs Crvena Zvezda`, `Olympiacos Piraeus vs Fenerbahce Istanbul`, `Paris Basketball vs Valencia Basket` — verified on `euroleaguebasketball.net`) plus **NBB CAIXA Jogo 14** (`União Corinthians vs Minas` — verified on `lnb.com.br`).
   - **Greyhounds (`+4` new UK afternoon bags):** `11:14 Kinsley` (`Limited Blue`), `11:36 Sheffield` (`Drumdoit Pixie`), `12:03 Kinsley` (`Ballymac Alyssa`), `12:14 Nottingham` (`Ferryforth Mary`) — explicitly flagged unverified where GBGB's Cloudflare gate blocks automated scraping, zero fields guessed.
   - **Ice Hockey (`+3` new SHL games + `1` consensus update):** Full 6-game **2026-10-22 SHL** slate completed with `IF Björklöven vs IF Malmö Redhawks`, `Rögle BK vs Frölunda HC`, and `Växjö Lakers HC vs Luleå HF` — all 6 verified at `19:00 CEST` on official `stats.swehockey.se` with complete 14-club standings.
   - **Tennis (`+3` new matches + `1` consensus break):** **ATP Almaty Open QF** (`[7] Stefanos Tsitsipas vs James Duckworth`), **ATP Lyon Grand Prix Auvergne-Rhône-Alpes QF** (`Corentin Moutet vs [4] Tommy Paul`) — both verified directly against live `atptour.com` draw sheets — plus `Talia Gibson vs Ashlyn Krueger` (left blank/unverified where `wtatennis.com` serves a client-rendered shell).
   - **Handball (`+1` new ASOBAL match + `3` consensus updates):** `IRUDEK Bidasoa Irun vs BM. Caserío Ciudad Real` (`Liga NEXUS ENERGÍA ASOBAL Jornada 7`, `23 Oct 2026 19:00 CEST`, `Pabellón Artaleku, Irun`) verified on official `cdbidasoa.eus` and `asobal.es`.

2. **9 previously unverified rows upgraded to primary governing-body verification (`docs/verifications-5cef1e25.json`):**
   - `HBL-24` (`Estonia W vs Kosovo W`) -> verified on `eurohandball.com` (**100% of Handball rows now officially verified: 33/33!**)
   - `HBL-28` (`Skive fH vs Aalborg Håndbold`) -> verified on `aalborghaandbold.dk` + `tophaandbold.dk`
   - `BKB-24` (`Fortaleza BC vs Pinheiros`) -> verified as `Basquete Cearense x Pinheiros` on `lnb.com.br`
   - `CRK-05` (`Mpumalanga Rhinos vs SA Emerging`) -> verified as `M.P. Rhinos vs CSA High Performance` on `cricket.co.za` (**100% of Cricket rows now officially verified: 15/15!**)
   - `CRK-06` (`Eastern Storm vs Tuskers`) -> verified on `cricket.co.za`
   - `MTR-01` (`F1 Drivers Championship 2026`) -> verified with live 2026 standings (`1. Kimi Antonelli 340 pts, 2. George Russell 238 pts, 3. Lewis Hamilton 229 pts, 4. Max Verstappen 221 pts`) on `formula1.com` (**100% of Motor Racing rows now officially verified: 2/2!**)
   - `GLF-05` (`Webex Players Series South Australia`) -> verified on `golf.com.au`
   - `GLF-06` (`Senior Italian Open`) -> verified on `legendstour.com`
   - `GLF-08` (`Hong Kong Open`) -> verified on `asiantour.com`

3. **Zero-inference policy violation caught & repaired (`DRT-11`):**
   - `DRT-11` (`Danny Noppert vs Jermaine Wattimena`, graded `HIGH`) previously carried `"Fri 23 Oct 2026, 19:45 CEST (inferred from the official running order)"`, directly violating the user's explicit instruction: *"Never infer or fill in values."* Replaced with the exact published PDC session start time (`"Fri 23 Oct 2026, Evening Session from 19:00 CEST, Westfalenhallen Dortmund"`) and logged on `Flagged for Review`.

4. **4 new real-world OLBG vs governing-body irregularities uncovered & flagged for review:**
   - **Estonia W vs Kosovo W (`HBL-24`) reversed home-ice/home-court reality:** OLBG lists `Estonia W` first as home team, whereas EHF confirms **both Phase 1 World Championship Qualification legs (`23 & 24 Oct 2026`) are played in Prishtina, Kosovo** (`eurohandball.com`).
   - **Mpumalanga Rhinos vs SA Emerging (`CRK-05`) governing-body team rename:** OLBG lists `"SA Emerging"`, whereas Cricket South Africa enters the team officially as **`CSA High Performance`** (`cricket.co.za`).
   - **Fortaleza BC vs Pinheiros (`BKB-24`) governing-body club registration:** OLBG lists `"Fortaleza BC"`, whereas Liga Nacional de Basquete registers the club officially as **`Basquete Cearense`** (`lnb.com.br`).
   - **Senior Italian Open (`GLF-06`) tournament close & format mismatch:** OLBG lists `25 Oct 2026`, whereas the Staysure Legends Tour plays the 54-hole **Stableford** championship **`22–24 Oct 2026`** at San Domenico Golf, Puglia (`legendstour.com`), with Sunday `25 Oct` reserved for the post-event Pro-Am.
