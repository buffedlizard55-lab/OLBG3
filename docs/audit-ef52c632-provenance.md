# Capture-to-publication provenance audit

Publication clock audited: **2026-10-26T20:23:00Z**. This is a deterministic reread of committed files, not a fresh capture or a certification of current sporting facts.

**Result: REVIEW — 0 errors, 15 warnings, 136 informational observations.**

A clean lineage result means the published data can be reproduced from the declared inputs. It does not prove that an old listing is still available, that a start time is officially confirmed, or that a selection is advisable. Blank source values remain blank; conflicting observations remain visible.

## Coverage

| Measure | Count |
|---|---:|
| Raw capture observations | 1119 |
| Distinct captured events | 523 |
| Observations not selected by first-capture-wins | 596 |
| Published match rows accounted for | 523 |
| Published originated-line rows accounted for | 523 |
| Root written predictions / HIGH rows | 93 / 0 |
| OLBG-board written predictions / HIGH rows | 61 / 2 |
| Verification source-register entries | 262 |

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
| [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv) | 142 |
| [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv) | 97 |
| [raw/olbg-harvest-20261023T1700Z.tsv](../data/raw/olbg-harvest-20261023T1700Z.tsv) | 154 |
| [raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv](../data/raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv) | 109 |
| [raw/olbg-harvest-20261023T1630Z.tsv](../data/raw/olbg-harvest-20261023T1630Z.tsv) | 3 |
| [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv) | 16 |
| [raw/olbg-harvest-20261024T1755Z-30053696.tsv](../data/raw/olbg-harvest-20261024T1755Z-30053696.tsv) | 2 |

## Warnings for manual review

### Conflicting source clocks

Both observations are retained. The selected publication value follows the declared first-capture-wins rule; the conflict is not silently resolved and no official start is inferred.

#### [188845](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845)

- **2026-10-24T23:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L18](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L18), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845).
- **2026-10-24T23:00:00.000Z** — [raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L18](../data/raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L18), fetched 2026-10-24T17:07:26Z; [OLBG event](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845).
- **2026-10-23T23:00:00.000Z** — [raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L25](../data/raw/olbg-supplement-20261023T2133Z-b322f52e.tsv#L25), fetched 2026-10-23T21:33:06Z; [OLBG event](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845).
- **2026-10-24T23:00:00.000Z** — [raw/olbg-harvest-20261024T1755Z-30053696.tsv#L17](../data/raw/olbg-harvest-20261024T1755Z-30053696.tsv#L17), fetched 2026-10-24T17:55:00Z; [OLBG event](https://www.olbg.com/betting-tips/Cricket/All_Cricket/All_Events/Toronto_Kings_vs_Vancouver_Guardians_T20/7?event_id=188845).

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

#### [32407](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Stephen_Bunting/15?event_id=32407)

- **2026-10-25T13:15:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L34](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L34), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Stephen_Bunting/15?event_id=32407).
- **2026-10-25T11:00:00.000Z** — [raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L36](../data/raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L36), fetched 2026-10-24T17:07:26Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Stephen_Bunting/15?event_id=32407).
- **2026-10-25T11:00:00.000Z** — [raw/olbg-harvest-20261024T1755Z-30053696.tsv#L34](../data/raw/olbg-harvest-20261024T1755Z-30053696.tsv#L34), fetched 2026-10-24T17:55:00Z; [OLBG event](https://www.olbg.com/betting-tips/Darts/All_Darts/All_Events/Gerwyn_Price_vs_Stephen_Bunting/15?event_id=32407).

#### [37101](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Montes_Claros_vs_Sada_Cruzeiro/21?event_id=37101)

- **2026-10-26T22:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L135](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L135), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Montes_Claros_vs_Sada_Cruzeiro/21?event_id=37101).
- **2026-10-26T23:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L128](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L128), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Montes_Claros_vs_Sada_Cruzeiro/21?event_id=37101).

#### [37102](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Norde_Volei_vs_Volei_Renata/21?event_id=37102)

- **2026-10-27T00:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L136](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L136), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Norde_Volei_vs_Volei_Renata/21?event_id=37102).
- **2026-10-27T01:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L129](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L129), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Volleyball/All_Volleyball/All_Events/Norde_Volei_vs_Volei_Renata/21?event_id=37102).

#### [902172](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172)

- **2026-10-27T06:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L123](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L123), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172).
- **2026-10-27T02:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L109](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L109), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172).
- **2026-10-27T02:00:00.000Z** — [raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L182](../data/raw/olbg-harvest-20261024T1707Z-a30d9bdb.tsv#L182), fetched 2026-10-24T17:07:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172).
- **2026-10-27T02:00:00.000Z** — [raw/olbg-harvest-20261024T1755Z-30053696.tsv#L165](../data/raw/olbg-harvest-20261024T1755Z-30053696.tsv#L165), fetched 2026-10-24T17:55:00Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Leylah_Fernandez_vs_Himeno_Sakatsume/3?event_id=902172).

#### [902232](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Stan_Wawrinka_vs_Jiri_Lehecka/3?event_id=902232)

- **2026-10-27T18:30:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L132](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L132), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Stan_Wawrinka_vs_Jiri_Lehecka/3?event_id=902232).
- **2026-10-26T10:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L105](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L105), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Stan_Wawrinka_vs_Jiri_Lehecka/3?event_id=902232).

#### [902233](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Novak_Djokovic_vs_Ugo_Humbert/3?event_id=902233)

- **2026-10-28T10:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L133](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L133), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Novak_Djokovic_vs_Ugo_Humbert/3?event_id=902233).
- **2026-10-26T10:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L104](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L104), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Novak_Djokovic_vs_Ugo_Humbert/3?event_id=902233).

#### [902238](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alejandro_Tabilo_vs_Rafael_Jodar/3?event_id=902238)

- **2026-10-27T13:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L130](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L130), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alejandro_Tabilo_vs_Rafael_Jodar/3?event_id=902238).
- **2026-10-26T10:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L98](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L98), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alejandro_Tabilo_vs_Rafael_Jodar/3?event_id=902238).

#### [902240](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alex_Michelsen_vs_Botic_Van_De_Zandschulp/3?event_id=902240)

- **2026-10-27T14:00:00.000Z** — [raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L131](../data/raw/olbg-harvest-20261026T2020Z-ef52c632.tsv#L131), fetched 2026-10-26T20:20:26Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alex_Michelsen_vs_Botic_Van_De_Zandschulp/3?event_id=902240).
- **2026-10-26T10:00:00.000Z** — [raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L99](../data/raw/olbg-harvest-20261024T2225Z-1815f0b1.tsv#L99), fetched 2026-10-24T22:25:15Z; [OLBG event](https://www.olbg.com/betting-tips/Tennis/All_Tennis/All_Events/Alex_Michelsen_vs_Botic_Van_De_Zandschulp/3?event_id=902240).

Manual review lead for the European Championship rows: the [official PDC schedule announcement](https://www.pdc.tv/news/2026/october/19/2026-machineseeker-european-championship-schedule-confirmed/) was attempted, but the retrieved content contained cookie/privacy boilerplate rather than usable schedule evidence. It therefore does not resolve these clocks.

### Probability-field semantics

data/schema.md says our_match_probability describes the OLBG consensus selection, but generated rows set it equal to our_pick_probability even when the selection differs. The report identifies **113 affected rows**. The schema owner must choose and document the intended meaning; this audit does not rewrite either the schema or generated lines.

Review [data/schema.md](../data/schema.md#linesjson-fields) and [data/lines.json](../data/lines.json).

### Other warnings

| Code | Finding |
|---|---|
| `capture_decimal_price_invalid` | OLBG decimal price must be numeric and exceed 1 when present: 'SP' |

## Informational differences

These differences are retained for review but are not publication errors by themselves. In particular, the builder does not overwrite an existing event when a later supplement changes its market or displayed price.

| Code | Count | Meaning |
|---|---:|---|
| `capture_market_changed` | 26 | Nonempty headline-market labels differ across captures. |
| `capture_price_changed` | 109 | Displayed decimal prices differ across captures; no independent bookmaker price is inferred. |
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
