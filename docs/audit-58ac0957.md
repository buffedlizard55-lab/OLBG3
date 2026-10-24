# Written-pick quality audit — session-58ac0957

**Audit date:** 2026-10-24 (UTC)

**Owner:** `session-58ac0957` / `task-58ac0957-written-pick-quality-gate`

**Scope:** independent prose-quality checks across both tracks, plus fresh official-source reads for the 11 `/olbg/` HIGH predictions. No fixture, price, confidence, prediction, harvest, rendering or generated-HTML input was edited by this task.

## Executive result

The new deterministic gate passes the current combined inputs: **142 written pieces (24 HIGH, 118 analysis), zero HIGH violations and one analysis-only duplicate warning**. Fourteen focused unit tests pass, and `tools/check_site.py` passes with the independent gate enabled.

The manual source review is intentionally not reduced to that green result. It found:

1. **Two contradicted HIGH history claims.** Official EHF match pages disprove the Round 1 statements in `HAN-12134` and `HAN-12133`. These are factual corrections, not style preferences.
2. **Several citation-coverage gaps.** Other checked facts agree with official pages, but some picks label one URL as though it also contained a second kind of evidence (for example, standings plus a box score) or omit the direct page carrying the claim.
3. **One unconfirmed surface detail.** `VOL-36995` says “home taraflex”; neither cited page read states the surface.
4. **One archived cross-track duplicate.** `BKB-22` and `BKB-535928` have identical analysis bodies. It is a warning because neither is HIGH.
5. **One official-source internal discrepancy.** Volleyball World Match `30001` prints set scores and standings totaling 90 Monza points, while its team-stats row prints 91. This audit does not select or invent a replacement value.

The two contradictions and the correction handoff are recorded in `data/raw/probe-58ac0957/source-review.json`. The active shared-data owner was notified through [PR #169 comment](https://github.com/buffedlizard55-lab/OLBG3/pull/169#issuecomment-6387685549), because prediction and flag inputs are outside this task's non-overlapping edit scope. **A green structural gate is not represented as proof that those two historical statements are true.**

## Contradicted HIGH claims

| Pick | Published claim | Direct official evidence | Required review action |
| --- | --- | --- | --- |
| `HAN-12134` | Aalborg “already beat Paris Saint-Germain in Round 1 at Aalborg.” | [EHF Round 1 match page](https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101025/AalborgH%C3%A5ndbold-ParisSaintGermain/) records **Aalborg 33:33 PSG** on 9 September. | Remove/correct the claimed win or carry the piece as explicitly flagged; do not repeat it as fact. |
| `HAN-12133` | “Dinamo also won the Round 1 meeting in Bucharest.” | [EHF Round 1 match page](https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101056/DinamoBucuresti-MontpellierHandball/) records **Dinamo 23:27 Montpellier** on 10 September. | Remove/correct the claimed win or carry the piece as explicitly flagged; do not repeat it as fact. |

Other freshly checked Round 1 handball statements were supported: [Sporting 43:33 GOG](https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101039/SportingClubedePortugal-GOG/) and [Melsungen 33:31 Vardar](https://ehfcl.eurohandball.com/men/2026-27/matches/details/202711020101021/MTMelsungen-HCVardar1961/). This is why the findings are per claim, not a blanket judgement on every handball pick.

## Per-pick source review

“Supported” below means only the listed prose facts were found on the official pages read. It does not mean a price is proven value or that an outcome is known.

| Pick | Review result | Finding / citation action |
| --- | --- | --- |
| `MTR-913` | Facts supported; citation drift | The [direct FP1 report](https://www.formula1.com/en/latest/article/fp1-leclerc-fastest-in-first-practice-for-the-united-states-gp-ahead-of-verstappen-and-norris.125WlaFK7K1mXXyLgb93ui) confirms Leclerc 1:36.052, Verstappen +0.084, Norris +0.245 and Russell +0.326. The linked race hub now displays FP2, so add the direct FP1 URL. |
| `GFA-3530` | Supported | Cork GAA confirms the final, venue and published knockout routes. The Carbery margin remains unstated, correctly avoiding an invented scoreline. |
| `VOL-36997` | Supported | Volleyball World confirms the 25 October fixture, Cuneo 2-3 Perugia, 25-23 deciding set, Reggers 18, Semeniuk 13 and Perugia's seven blocks. |
| `VOL-36995` | Review wording | Fixture and table claims agree. “Home taraflex” was not present in the cited schedule/standings reads and needs an official surface citation or removal. |
| `VOL-36996` | Facts supported; citation gap | [Match 30001](https://en.volleyballworld.com/volleyball/competitions/superlega/schedule/30001/) supports the 47-45 attack, 13-2 block and scorer claims. Add it directly; the current standings URL is not also the box score. The official 90/91 discrepancy is preserved in the receipt. |
| `RGU-609581` | Supported | URC sources agree on St. Helen's, the 19:45 IRE & UK start, Dragons 31-38 Ospreys and the published table figures. |
| `HAN-12138` | Facts supported; citation gap | Plock 33:32 Vardar, Melsungen 28:26 Plock, Nantes 27:33 Vardar and Cojean's quote are supported. Add the Wednesday and Round 4 pages instead of presenting the Thursday review as both reviews. |
| `HAN-12130` | Facts supported; citation gap | Round 5, table and Melsungen's 33:31 Round 1 win are supported. The standings URL is not the Round 5 review named in its label; add the review/result links. |
| `HAN-12134` | **Contradicted HIGH** | Round 5/table claims agree; the Round 1 Aalborg win is false (33:33). See above. |
| `HAN-12129` | Facts supported; citation gap | Sporting's 42:40 Kristianstad result, 14-goal Costa performance, table figures and 43:33 Round 1 win over GOG agree. Add direct standings/result links. |
| `HAN-12133` | **Contradicted HIGH** | Round 5, injury/red-card and table claims agree; the Round 1 Dinamo win is false (23:27). See above. |

The exact chunks read and factual excerpts are in `data/raw/probe-58ac0957/source-review.json`. The reader does not provide exact request timestamps, so the receipts record the exact UTC date and explicitly do not invent times. Limited reads are identified as limited; in particular, only chunk 0 of the Cork results index was read.

## Independent gate design

New command:

```bash
python3 scripts/check_prediction_quality.py \
  --manifest data/raw/probe-58ac0957/prediction-quality-manifest.json
```

It adds the following controls without replacing the established board/site rules:

- **Selection/body agreement for HIGH:** the selection must identify the row's actual pick, and a recommendation sentence in the body must endorse that same pick. Full-name aliases are allowed only after row/selection agreement; they cannot excuse a swapped side.
- **Prohibited prose terms:** the standalone words `model` and `verified` fail in a headline, selection or body. Longer words such as `modelling` and `unverified` are not false positives.
- **Official-document diversity for HIGH:** at least two distinct reviewed official documents are required. OLBG and reviewed secondary outlets do not count as sporting-governing-body evidence; fragments of one page do not count as two documents.
- **Near-duplicate detection:** four-word-shingle Jaccard and token-sequence similarity are compared globally. Any pair involving HIGH is release-blocking; analysis-only pairs are warnings. Exact duplicates within one track remain the existing checkers' responsibility, avoiding duplicate errors.
- **Deterministic manifest:** every piece has track/id/status, word count, body hash, selection agreement, prohibited-term findings, canonical official documents and near-duplicate details. There is deliberately no generated timestamp.

The existing 30-word floor, source URL checks, price quotes, confidence/status agreement, release eligibility and exact duplicates within each track remain in force. `tools/check_site.py` calls `run_quality_gate(ROOT)` and appends its errors; it does not write or rewrite prediction data.

## Local verification

After rebasing onto the merged 2026-10-24 refresh (`origin/main` `330b31e`):

```text
python3 scripts/check_prediction_quality.py
written-pick quality: predictions=142 high=24 analysis=118 errors=0 warnings=1
WARN quality near-duplicate olbg/BKB-535928 <-> root/BKB-22
PASS

python3 -m unittest tests.test_prediction_quality -q
Ran 14 tests ... OK

python3 tools/check_site.py
pages: 20  fixtures: 223  lines: 223  high: 11  predictions: 49  flagged: 200
written-pick quality: predictions=142 high=24 warnings=1
All checks passed.
```

Full local verification after generating the gitignored `site/` artifact in workflow order (`scripts/build.py` then `scripts/build_site.py`):

```text
python3 -m unittest discover -s tests -v
Ran 338 tests ... OK (skipped=26)

python3 scripts/check_board.py
rows=367 fixtures=319 outright_or_race=48 verified=278 priced=318 predictions=93
PASS

python3 scripts/check.py
PASS: 53 fixture rows; official hosts, blank betting fields, unique IDs and all internal links checked.

python3 scripts/check_links.py
pages=110 local_links_checked=2552 broken=0
```

An earlier direct unit-test invocation had three missing-`site/` errors and the first link invocation had 114 missing scaffold links because the gitignored artifact had not been built in workflow order. The artifact was generated, not hand-edited, and the same checks then passed as recorded above. No tracked HTML changed.

PR, merge and Pages evidence is recorded in `COORDINATION.md`; flagged factual/citation irregularities are not silently reclassified as passing facts.
