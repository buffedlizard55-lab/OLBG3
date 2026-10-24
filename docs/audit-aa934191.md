# Freshness and pick-navigation audit — 2026-10-24

## Scope and evidence boundary

This pass advances the publication/release-evaluation clock only; it does not renew any OLBG capture, official observation, price, injury report, result, or statistic. The latest committed OLBG harvest with rows is `data/raw/olbg-harvest-20261023T1700Z.tsv` (capture timestamp 2026-10-23T17:00Z). The previously committed publication clock was 2026-10-23T22:27Z. The clock was advanced to 2026-10-24T17:08Z so starts that have passed cannot remain in the static release count. It is not a source-observation timestamp.

## Live OLBG comparison

At 2026-10-24T17:08Z, OLBG's public pages were read:

- [Baseball betting tips](https://www.olbg.com/betting-tips/Baseball/12) displayed TB Rays @ MIL Brewers, event ID `160792`, a “Today 20:00” listing, and the Money Line market. The repository's current Baseball record is `BSB-160789` / event ID `160789`.
- [Tennis betting tips](https://www.olbg.com/betting-tips/Tennis/3) displayed upcoming events including IDs `902171`, `902207`, `902251`, `902175`, `902173`, and `902172`. The repository's committed Tennis event IDs are from the earlier `902147`–`902168` set.
- [OLBG's betting tips hub](https://www.olbg.com/betting-tips) was also read and showed its current, mixed-sport feed.

These are direct observations of different listing snapshots, not proof that any old fixture was canceled, settled, or unavailable. The event IDs and OLBG's relative “Today/Tomorrow” labels were not transformed into official starts or independent market lines. No new match or pick was added. Re-capturing and officially rechecking all 15 in-scope sports remains necessary before the board can claim a refreshed complete list.

## Output and verification

- `data/publication.json` now reads `2026-10-24T17:08:00Z`; no source-check timestamps or quoted evidence were touched.
- Rebuilt both research tracks from committed inputs. OLBG track: 223 fixtures; 11 remain HIGH after the publication-time release gate. The daily five-per-sport target is met by one sport; 64 picks short of the 75-pick target. No unsupported picks were manufactured.
- Root track's five HIGH picks and the OLBG track's eleven HIGH picks are distinct across the two tracks only where the accounting says they are; the shared brief recomputes to 11 distinct union picks. Counts are published as research release counts, not betting performance claims.
- `python scripts/check_board.py`, `python tools/check_site.py`, `python scripts/check.py`, `python scripts/check_links.py` passed. The initial unit suite exposed a clock-dependent historical regression pin; it is corrected to evaluate the dated candidate scan at its recorded historical time. The full suite is rerun after that correction.

## Irregularity for review

`FL-199` is published on the Flagged for Review page. Current OLBG Baseball/Tennis listing IDs differ from the last committed harvest. Until a fresh capture and fixture-by-fixture official-source check are committed, the existing rows should be treated as a dated research snapshot rather than a complete current OLBG slate.

## Scope ambiguity: Gaelic Sports

The requested category “Gaelic Sports” is broader than the board's current `Gaelic Football` category. The existing repo scope explicitly excludes Hurling. The GAA's [official Our Games page](https://www.gaa.ie/the-gaa/games/our-games) lists Hurling and Gaelic football within Gaelic Games and also identifies Handball, Rounders, Camogie and Ladies Football. OLBG's live hub read on this pass displayed a Hurling event (Ballyhale Shamrocks v Tullaroan, event ID 714). No Hurling fixture or prediction is added here: its inclusion requires separate fixture, official form, and market verification. This mismatch is published as `FL-200` rather than silently representing Gaelic Football as every Gaelic sport.
