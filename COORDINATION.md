# COORDINATION — OLBG3 shared task board

Read this file before working. Claim a task (session ID + file scope) and push the claim
immediately. Never start a task another live session has claimed. Scopes must not overlap.

## Session roster

| Session ID | Branch (Arena-managed) | Role | Status |
|---|---|---|---|
| `S-20261021-A` | `arena/9590abcf-olbg3` | worker **and** final integration session | active |

> Note on branch naming: the brief suggests `session-<id>/<task>` branches. This session runs
> inside an Arena workspace whose branch is fixed to `arena/9590abcf-olbg3` and may not be
> renamed or switched away from. All work happens on that branch. No other session branches
> existed at start (`git branch -a` → `main`, `arena/9590abcf-olbg3` only), so no scope
> collisions were possible in this run.

## Task board

| # | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T1 | Scaffolding: repo layout, data schema, coordination board | done | S-20261021-A | `README.md`, `COORDINATION.md`, `data/schema.md` |
| T2 | Harvest OLBG fixture list per sport; coverage matrix incl. excluded sports | done | S-20261021-A | `data/matches.json`, `data/raw/`, `data/meta.json`, `data/excluded.json` |
| T3 | Originate own lines (moneyline / handicap / total) + pick + confidence | done | S-20261021-A | `data/lines.json`, `data/model.md`, `tools/originate.py` |
| T4 | High-confidence predictions (≥30 words, verified facts, source links) | done | S-20261021-A | `data/predictions.json` |
| T5 | Flagged-for-review register | done | S-20261021-A | `data/flagged.json` |
| T6 | Static site build (`docs/`) + link/integrity checker | done | S-20261021-A | `tools/`, `docs/`, `.github/workflows/` |
| T7 | Integration: merge, re-verify combined data, publish, PR + merge | in progress | S-20261021-A | `main` (via PR) |

## Log

### 2026-10-21 — S-20261021-A — T1 done
- Repo at `96f089b` contained only a 7-byte `README.md`. No prior data, no site, no CI.
- Created layout: `data/` (JSON + schema), `tools/` (harvest/build/verify), `docs/` (site).
- Evidence: `git log --oneline` → single commit "Initial commit"; `ls -la` → `README.md` only.

### 2026-10-21 — S-20261021-A — T2 done
- Method constraint (verified, not assumed): the sandbox HTTP client can only reach the hosts on
  its allowlist. `curl https://www.olbg.com/` returned `SSL_ERROR_SYSCALL` (exit 35); espn.com and
  bbc.co.uk failed identically, so this is not an OLBG block. Pages were therefore retrieved with
  the agent's page-retrieval tool and transcribed by hand, with the retrieval timestamp on every row.
- 16 OLBG sport pages retrieved (all sports + one per included sport). 137 fixtures captured across
  15 included sports. Sport ids taken from the OLBG sport list: Cricket/7, Tennis/3, Basketball/4,
  Snooker/8, Darts/15, Rugby_Union/9, Rugby_League/10, Ice_Hockey/13, Baseball/12, Volleyball/21,
  Handball/20, Golf/5, Motor_Racing/14, Gaelic_Football/25, Greyhounds/28.
- Excluded sports located and recorded with rows in `data/excluded.json`: Football/1 (6 rows seen),
  Boxing/16 (UFC/MMA fight cards, 1 row), Hurling/26 (1 row), Horse_Racing/2 (2 rows). Cycling/17,
  American_Football/11 and Specials had no live rows at retrieval time — recorded as such.
- Coverage limit found and documented: every sport page paginates behind "Load More Tips", so only
  the first page is in scope here (FL-008).

### 2026-10-21 — S-20261021-A — T3 done
- Model implemented in `tools/originate.py`, documented in `data/model.md`: tip split →
  Beta(2,2) shrinkage (strength 4) → sport-specific home-edge logit shift → price at 5% hold;
  handicap from `−Φ⁻¹(p) × σ_sport`; totals from a documented per-sport baseline.
- Output: 137/137 fixtures have a pick; 111 have a two-way price from a real split, 107 have a
  handicap, 113 a total. Outright markets carry no price on purpose (field size not published).
- Confidence ladder: 5 high / 24 medium / 108 low. Low is deliberate for one-tip samples and for
  OLBG rows whose highlighted market was not the winner market.

### 2026-10-21 — S-20261021-A — T4 done
- 5 high-confidence predictions, 71–80 words each, each naming its selection explicitly, each with
  the exact source for every fact it asserts:
  - BSB-160789 Brewers ML — mlb.com schedule + ESPN game page (records 103-59 / 98-64, NLCS sweep,
    ALCS 4-2, first World Series since 1982).
  - BKB-534889 Wizards ML — nba.com/wizards schedule announcement + CBS preseason results.
  - ICH-199897 Sabres ML — CBS/ESPN team result pages (4-3-2 and 2-6-3, exact scorelines).
  - SNO-9934 Higgins — snooker.org round-one results (4-1 with a 121 break vs Highfield;
    Jones 4-1 vs Ford) + WST match centre + BBC event guide.
  - DAR-32337 Humphries — pdc.tv official schedule (last year's runner-up, Westfalenhalle 22-25 Oct)
    + 2026 World Grand Prix final 6-4 over Price.
- Deliberate gap, logged: no prediction was written for cricket/tennis/volleyball/handball rows
  because team form and squads could not be verified fixture-by-fixture from official sources in
  this pass. Those rows are capped at medium (FL-010, FL-017).

### 2026-10-21 — S-20261021-A — T5 done
- 17 flagged items, each with sources, published on the site's "Flagged for review" page.
  Headline findings: OLBG clock times carry no timezone and are internally inconsistent (FL-002);
  the same golf tournament appears with two different dates on two OLBG pages (FL-003); course par
  is reported as both 71 and 72 (FL-005); 111 of 137 rows have no competition name anywhere in the
  source (FL-006); three rows were truncated at the page boundary (FL-007); Gaelic football is not
  in the exclusion list and needs a decision (FL-001).

### 2026-10-21 — S-20261021-A — T6 done
- `docs/` holds 21 generated pages: dashboard, lines & picks (filterable/sortable), 5 prediction
  cards, all-matches table, method & sources, flagged register, and 15 per-sport pages.
- `tools/check_site.py` enforces: no broken internal link, no external host outside the reviewed
  allowlist, every data row has a source link, every fixture/line/prediction/flag is rendered,
  predictions ≥30 words and high-confidence, no placeholder text. It caught two unreviewed hosts
  (unitedrugby.com, ehfcl.eurohandball.com) during development, which were then reviewed and added.
- CI: `.github/workflows/build-and-publish.yml` rebuilds the data, runs the checks, fails if the
  committed data/site is stale, and publishes `docs/` to `gh-pages`.

### 2026-10-21 — S-20261021-A — T7 in progress
- Next: PR from `arena/9590abcf-olbg3` → `main`, merge, confirm the Pages workflow publishes to
  `gh-pages`, record the PR link and merge result here.

## Sources for the whole run

Full register with per-claim quotes: `data/verifications.json` (26 source records, 26 event-level
verification records). Primary classes used: OLBG (publisher, for every harvested field), pdc.tv,
mlb.com, nba.com, wst.tv/snooker.org, europeantour.com, unitedrugby.com, ehfcl.eurohandball.com,
atptour.com; secondary corroboration only from ESPN, CBS Sports, BBC, SBS, Wikipedia, cricinfo.

## Irregularities carried forward

See `data/flagged.json`. Nothing there blocks merge: no value is invented, blanks stay blank, and
every flagged item is published with its source so it can be reviewed after the site is live.
