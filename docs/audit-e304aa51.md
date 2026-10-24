# Fresh-evidence and final-integration audit — session e304aa51

**Audit clock:** 2026-10-24T22:33:00Z  
**Branch:** `arena/e304aa51-olbg3`  
**Evidence boundary:** Source responses were captured by the repository's GitHub runner. A successful fetch proves only what that URL served at that time. Blank fields were not inferred.

## Executive result

The current OLBG audit track now derives from one populated snapshot rather than a current primary plus old supplements:

| Item | Result |
|---|---:|
| Live listing endpoints requested | 18 |
| Rendered cards before event de-duplication | 142 |
| Unique current event IDs | 124 |
| Sports with current rows | 12 |
| Current rows matched to a fresh official NHL/MLB payload | 15 |
| Current `/olbg/` HIGH rows | 5 |
| Distinct live HIGH fixtures across both tracks | 13 |
| Brief target | 75 |
| Honest shortfall | 62 |
| Broken internal links | 0 |

The current primary is `data/raw/olbg-harvest-20261024T2224Z-e304aa51.tsv`. Older captures remain immutable under `data/raw`, but their rows are not carried onto the current `/olbg/` board. Golf, Snooker and Motor Racing returned zero cards in this capture and remain explicit coverage gaps.

## Pakistan v England — event 188838

Two separate write-ups publish **Pakistan to win at 1.60 (-167)** for the 25 October Lahore ODI.

Facts actually used:

- The [ECB fixture notice](https://www.ecb.co.uk/news/4594465/how-to-watch-and-follow-the-england-men-v-pakistan-and-sri-lanka) prints: “25 October - England Men v Pakistan, Lahore (8.00am GMT).” This supports `2026-10-25T08:00:00Z` and the city, but not a stadium.
- The [ICC men's ODI rankings](https://www.icc-cricket.com/rankings/team-rankings/mens/odi), rank date 24 October 2026, record Pakistan on 103 rating points and England on 93.
- The [ICC recent-match report](https://www.icc-cricket.com/news/pakistan-youngster-joins-elite-odi-group-with-superb-haul) records Pakistan 302/9, an 87-run win, and Arafat Minhas's 59 from 58 balls and 6/40.
- The current OLBG capture prints Pakistan as the selection on 9 of 15 tips and a displayed 2.35 price. That captured price is shown as OLBG's observation, not reused as this project's originated line.

The venue field remains blank. None of the cited governing-body documents names a stadium for this fixture. The cited documents also do not supply a current injury bulletin, so neither prediction asserts an injury or player-availability fact.

## Defects reproduced and repaired

### Fresh-primary promotion

`data/meta.json` had remained pinned to the 2026-10-23 primary despite newer populated evidence. Promotion now:

1. tries the newest capture's normal SSR cards;
2. retries Svelte hydration only if SSR is empty;
3. skips a capture if both modes produce no rows;
4. promotes a newer non-empty TSV;
5. records replaced-primary metadata under `archived_primary_harvests`; and
6. clears `previous_harvest`, `previous_harvests_extra` and `supplementary_harvests`.

A regression compares all 124 current harvest event IDs with all 124 `data/matches.json` event IDs.

### Official-probe provenance

The verifier previously used fixed 2026-10-23 identifiers and paths even when reading a later probe. It now derives the observation timestamp, source IDs, probe files and session note from the selected manifest. The current matched records use:

- `S-NHL-API-20261024T222540Z` — [NHL schedule API](https://api-web.nhle.com/v1/schedule/2026-10-24)
- `S-MLB-API-20261024T222540Z` — [MLB schedule API](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-24&endDate=2026-10-26&hydrate=team,linescore,probablePitcher)

Nine NHL cards did not match the fresh league payload and remain unverified.

### Starting-price label

The Greyhound card `GRY-690043` prints `SP`, not a numeric decimal. The first fresh rebuild attempted to parse that label as a float and stopped. The current row preserves `olbg_odds_raw: "SP"`, publishes a blank decimal and states that no value was inferred.

### Cited-page evidence

The previous cited-page collector fetched release-clock URLs only. It now includes every non-OLBG source linked by a HIGH prediction on both tracks, records which pieces reference each URL, and uses a URL hash in each filename.

The older `data/raw/cited-20261024T2226Z` run decoded PDF bytes as UTF-8 text; those `.txt` files are retained only as historical evidence of the failed method. The repaired collector writes PDFs and other binary responses byte-for-byte and records their SHA-256 hashes. A new runner re-read is requested before final integration.

## Open disclosures

- **Five-per-sport quota:** 13 distinct current HIGH fixtures, shortfall 62. Only Ice Hockey reaches five. `brief.html` gives the mechanical blocker for every sport.
- **Zero-card sports:** Golf, Snooker and Motor Racing are not backfilled from an older capture.
- **Exact starts:** Darts, Snooker and Tennis still lack a retrievable exact timezone-qualified governing-body start for the candidate rows. “Not before” is not converted into an exact clock.
- **Pakistan v England venue:** Lahore is confirmed; the stadium is blank.
- **Cross-track selections:** four of 19 paired fixtures carry different selections. Both versions remain visible on `reconcile.html`; no tie-break was invented.

These items are published on `flagged.html` and do not block publication.

## Verification run

The final local integration cycle completed:

- `scripts/check_board.py`: PASS — 367 rows, 319 fixtures, 94 written root pieces.
- `tools/check_site.py`: PASS — 124 current `/olbg/` fixtures, five HIGH rows, nine pieces, 209 register items.
- Prediction quality: 103 total pieces, 18 HIGH across both files, zero warnings.
- Capture-to-publication provenance: **0 errors, 9 review warnings** (the disclosed `SP` label, one standing probability-schema wording conflict, and seven HIGH pieces whose separate release-clock URL is not duplicated in that piece’s source list).
- Unit tests: **397 passed**, 69 dated-snapshot skips, zero failures.
- `scripts/check.py`: PASS.
- `scripts/check_links.py`: **106 pages, 2,712 internal links, zero broken**.

PR, merge and deployed Pages evidence will be appended to `COORDINATION.md` after those operations complete.
