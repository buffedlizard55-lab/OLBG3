# Capture-to-publication provenance audit

Publication clock audited: **2026-10-24T18:10:00Z**. This is a deterministic reread of committed files, not a fresh capture or a certification of current sporting facts.

**Result: REVIEW — 0 errors, 14 warnings, 46 informational observations.**

A clean lineage result means the published data can be reproduced from the declared inputs. It does not prove that an old listing is still available, that a start time is officially confirmed, or that a selection is advisable. Blank source values remain blank; conflicting observations remain visible.

## Coverage

| Measure | Count |
|---|---:|
| Raw capture observations | 480 |
| Distinct captured events | 223 |
| Observations not selected by first-capture-wins | 257 |
| Published match rows accounted for | 223 |
| Published originated-line rows accounted for | 223 |
| Root written predictions / HIGH rows | 93 / 13 |
| OLBG-board written predictions / HIGH rows | 49 / 11 |
| Verification source-register entries | 260 |

## Method and precedence

1. Read the primary, carried, and supplementary captures declared by `data/meta.json`, including both v2 and v3 layouts.
2. Keep every observation with its raw path, line number, fetch time, listing URL, event URL, and all captured v3 fields.
3. Replay the builder's first-capture-wins rule, then apply event verification fields, explicit live overrides, and withdrawals.
4. Compare the reconstructed row with `matches.json`; compare every originated line with its match and recompute its price arithmetic.
5. Check both prediction tracks for row/status agreement, explicit HIGH selections, source metadata, prohibited terms, release-evidence linkage, and repeated prose.
6. Hash every input so another reviewer can tell whether a difference comes from the auditor or from changed data.

The auditor performs no network requests. Official-host classification comes from the committed source register; it is not a fresh content check. Later capture values are not automatically superior, and a difference from OLBG consensus is not an error: editorial priors, fades, outright analysis, non-winner markets, and explicit overrides are legitimate parts of the publication chain.

### Selected rows by capture

| Capture | Selected events |
|---|---:|
| [raw/olbg-harvest-20261023T1700Z.tsv](../data/raw/olbg-harvest-20261023T1700Z.tsv) | 177 |
| [raw/olbg-harvest-20261023T1630Z.tsv](../data/raw/olbg-harvest-20261023T1630Z.tsv) | 3 |
| [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv) | 43 |

## Warnings for manual review

### Conflicting source clocks

Both observations are retained. The selected publication value follows the declared first-capture-wins rule; the conflict is not silently resolved and no official start is inferred.

#### [32383](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Cameron_Menzies_vs_Gerwyn_Price/15?event_id=32383)

- **2026-10-24T17:15:00.000Z** — [raw/olbg-harvest-20261023T1700Z.tsv#L45](../data/raw/olbg-harvest-20261023T1700Z.tsv#L45), fetched 2026-10-23T16:21:00Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Cameron_Menzies_vs_Gerwyn_Price/15?event_id=32383).
- **2026-10-24T11:15:00.000Z** — [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L38](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L38), fetched 2026-10-23T21:33:06Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Cameron_Menzies_vs_Gerwyn_Price/15?event_id=32383).

#### [32384](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Stephen_Bunting_vs_Kim_Huybrechts/15?event_id=32384)

- **2026-10-24T17:15:00.000Z** — [raw/olbg-harvest-20261023T1700Z.tsv#L48](../data/raw/olbg-harvest-20261023T1700Z.tsv#L48), fetched 2026-10-23T16:21:00Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Stephen_Bunting_vs_Kim_Huybrechts/15?event_id=32384).
- **2026-10-24T11:15:00.000Z** — [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L41](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L41), fetched 2026-10-23T21:33:06Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Stephen_Bunting_vs_Kim_Huybrechts/15?event_id=32384).

#### [32385](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gian_van_Veen_vs_Luke_Woodhouse/15?event_id=32385)

- **2026-10-24T17:15:00.000Z** — [raw/olbg-harvest-20261023T1700Z.tsv#L46](../data/raw/olbg-harvest-20261023T1700Z.tsv#L46), fetched 2026-10-23T16:21:00Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gian_van_Veen_vs_Luke_Woodhouse/15?event_id=32385).
- **2026-10-24T11:15:00.000Z** — [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L39](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L39), fetched 2026-10-23T21:33:06Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gian_van_Veen_vs_Luke_Woodhouse/15?event_id=32385).

#### [32386](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ross_Smith_vs_Damon_Heta/15?event_id=32386)

- **2026-10-24T17:15:00.000Z** — [raw/olbg-harvest-20261023T1700Z.tsv#L47](../data/raw/olbg-harvest-20261023T1700Z.tsv#L47), fetched 2026-10-23T16:21:00Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ross_Smith_vs_Damon_Heta/15?event_id=32386).
- **2026-10-24T11:15:00.000Z** — [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L40](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L40), fetched 2026-10-23T21:33:06Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Ross_Smith_vs_Damon_Heta/15?event_id=32386).

Manual review lead for the European Championship rows: the [official PDC schedule announcement](https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/) was attempted, but the retrieved content contained cookie/privacy boilerplate rather than usable schedule evidence. It therefore does not resolve these clocks.

### HIGH release evidence absent from prediction source lists

These rows have an official release-evidence URL on the board, but that exact URL is not repeated in the written prediction's source list. This is a transparency follow-up, not proof that the analysis is wrong. No citation has been invented or silently added.

| Track | Match | Official release evidence | Listing |
|---|---|---|---|
| olbg | VOL-36995 | [source](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30005/) | [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Civitanova_vs_Padova/21?event_id=36995) |
| olbg | VOL-36996 | [source](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30005/) | [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Monza_vs_Verona/21?event_id=36996) |
| olbg | HAN-12138 | [source](https://ehfel.eurohandball.com/media/jqal4wt0/ehfcl-men-2026-27-group-phase-playing-times.pdf) | [OLBG event](https://www.olbg.com/betting-tips/Handball/All_Handball/All_Events/Wisla_Plock_vs_Nantes/20?event_id=12138) |
| root | MTR-01 | [source](https://www.formula1.com/en/latest/article/formula-1-msc-cruises-united-states-grand-prix-2026.2u6li2pzNhPzL3TSYaagrm) | [OLBG event](https://www.olbg.com/betting-tips/Motor_Racing/All_Motor_Racing/All_Events/USA_Grand_Prix/14?event_id=913) |
| root | VOL-27 | [source](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30002/) | [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Perugia_vs_Pordenone/21?event_id=36997) |
| root | VOL-28 | [source](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30005/) | [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Civitanova_vs_Padova/21?event_id=36995) |
| root | VOL-29 | [source](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30005/) | [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Monza_vs_Verona/21?event_id=36996) |
| root | BSB-160792 | [source](https://statsapi.mlb.com/api/v1/schedule?sportId=1&startDate=2026-10-24&endDate=2026-10-26&hydrate=team,linescore,probablePitcher) | [OLBG event](https://www.olbg.com/betting-tips/Baseball/MLB/MLB/TB_Rays_@_MIL_Brewers/12?event_id=160792) |

### Probability-field semantics

data/schema.md says our_match_probability describes the OLBG consensus selection, but generated rows set it equal to our_pick_probability even when the selection differs. The report identifies **68 affected rows**. The schema owner must choose and document the intended meaning; this audit does not rewrite either the schema or generated lines.

Review [data/schema.md](../data/schema.md#linesjson-fields) and [data/lines.json](../data/lines.json).

### Repeated prose across dashboard tracks

The same fixture can legitimately appear on both tracks, but word-for-word reuse still needs an editorial decision under the uniqueness requirement.

| OLBG-board row | Root row | Official sources on the written piece | Listing |
|---|---|---|---|
| BKB-535928 | BKB-22 | [EuroLeague official round-7 preview (dated fixture, players, recent games)](https://www.euroleaguebasketball.net/en/euroleague/news/game-center-round-7-el2627/); [EuroLeague official standings (conflicts explicitly held where noted)](https://www.euroleaguebasketball.net/en/euroleague/standings/) | [OLBG event](https://www.olbg.com/betting-tips/Basketball/European/Euroleague/Zalgiris_vs_Asvel_Lyon_Villeurbanne/4?event_id=535928) |

## Informational differences

These differences are retained for review but are not publication errors by themselves. In particular, the builder does not overwrite an existing event when a later supplement changes its market or displayed price.

| Code | Count | Meaning |
|---|---:|---|
| `capture_market_changed` | 14 | Nonempty headline-market labels differ across captures. |
| `capture_price_changed` | 31 | Displayed decimal prices differ across captures; no independent bookmaker price is inferred. |
| `prediction_near_duplicate_review` | 1 | Normalized word-trigram similarity merits a human prose review; it is not proof of duplication. |

## Review boundary and reproduction

- No capture, fixture, verification, override, line, prediction, flag, or generated HTML file is modified by this audit.
- The complete per-event observation chain and every issue's raw references are in [data/provenance_audit.json](../data/provenance_audit.json).
- Quota coverage, current OLBG availability, and live deployment are separate release checks; this report does not certify them.

Reproduce with:

```bash
python3 scripts/audit_provenance.py
python3 -m unittest tests.test_audit_4e26d590
```
