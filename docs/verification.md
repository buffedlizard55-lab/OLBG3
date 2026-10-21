# Verification log (summary)

Full row-by-row table: `verification.html` on the site, sourced from `data/official.json`.

## Verified against an official competition source — 10 rows

| Ref | Fixture | OLBG says | Official source says | Source |
|---|---|---|---|---|
| RGU-04 | Connacht v Zebre Parma | 23 Oct 14:45 | Fri 23 Oct 2026, 14:45, Dexcom Stadium, URC Round 4 | stats.unitedrugby.com/match-centre/2026-27/4 |
| RGU-07 | Bulls v Ulster | 24 Oct 07:45 | Sat 24 Oct 2026, 07:45, Loftus Versfeld | same |
| RGU-11 | Stormers v Scarlets | 24 Oct 10:00 | Sat 24 Oct 2026, 10:00, DHL Stadium | same |
| RGU-14 | Leinster v Munster | 24 Oct 13:00 | Sat 24 Oct 2026, 13:00, Aviva Stadium | same |
| IHO-06 | Sabres v Flyers | 19:37 | 21 Oct 2026, 7:30 PM EDT | nhl.com/schedule/2026-10-21 |
| IHO-07 | Senators v Panthers | 19:37 | 21 Oct 2026, 7:30 PM EDT | same |
| BKB-01 | Wizards v Bucks | 19:10 | 21 Oct 2026, 7:00 PM ET, Capital One Arena | nba.com/schedule?date=10/21/2026 |
| BKB-04 | Magic v Hawks | 19:10 | 21 Oct 2026, 7:00 PM ET, Kia Center | same |
| BKB-05 | Raptors v Bulls | 19:40 | 21 Oct 2026, 7:30 PM ET, Scotiabank Arena | same |
| BKB-09 | Pelicans v Pacers | 20:10 | 21 Oct 2026, 8:00 PM ET, Smoothie King Center | same |

Form data used by the model (verbatim, with sources):
* URC official table 2026/27 — 16 teams, PTS/PL/W/D/L/BP/PF/PA/DIFF/TF/TA/form.
* NHL.com standings dated 20 Oct 2026 — 6 teams transcribed (OTT, FLA, BUF, PHI + BOS, CAR for cross-checks).
* URC Round 3 results block (9–10 Oct 2026) — 8 final scores.

## Unverified — 104 rows
Reason: OLBG does not name the tournament for those fixtures (tennis, cricket, volleyball, darts, snooker, handball, Gaelic football, French rugby, European basketball, Austrian/Swedish hockey) and pulling every official tour/league fixture list was beyond this session. They keep their OLBG data and event link and are listed on Flagged for Review. **No field was filled by inference to make a row look complete.**

## Discrepancies found
1. OLBG start times are 7–10 minutes later than the official schedule on all 6 North American fixtures checked.
2. OLBG states no time zone, and the implied zone is not consistent between sports.
3. OLBG abbreviates club names (Bulls, Stormers, BUF Sabres) — aliased explicitly in `scripts/model.py`, no value altered.
4. Pagination means the captured rows are a first page, not a complete list, for 6 sports.
5. One handball row (FC Barcelona v Montpellier) was truncated on capture and dropped rather than reconstructed.
