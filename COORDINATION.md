# COORDINATION — OLBG3 shared task board

Read this file before working. Claim a task (session ID + file scope) and push the claim
immediately. Never start a task another live session has claimed. Scopes must not overlap.

## Session roster

| Session ID | Branch (Arena-managed) | Role | Status |
|---|---|---|---|
| `S-20261021-A` | `arena/9590abcf-olbg3` | worker **and** final integration session | active |

> Note on branch naming: the task brief suggests `session-<id>/<task>` branches. This
> session runs inside an Arena workspace whose branch is fixed to `arena/9590abcf-olbg3`
> and may not be renamed or switched away from. All work therefore happens on that
> branch. No other session branches existed at start (`git branch -a` → `main`,
> `arena/9590abcf-olbg3` only), so scope collisions were not possible in this run.

## Task board

| # | Task | Status | Owner | File scope |
|---|---|---|---|---|
| T1 | Scaffolding: repo layout, data schema, coordination board | done | S-20261021-A | `README.md`, `COORDINATION.md`, `data/schema.md` |
| T2 | Harvest OLBG fixture list per sport; build coverage matrix incl. excluded sports | in progress | S-20261021-A | `data/matches.json`, `data/sports.json`, `data/meta.json` |
| T3 | Originate own lines (moneyline / handicap / total) + pick + confidence | unclaimed | — | `data/lines.json` |
| T4 | High-confidence predictions (≥30 words, verified facts, source links) | unclaimed | — | `data/predictions.json` |
| T5 | Flagged-for-review register (unverified values, irregularities) | unclaimed | — | `data/flagged.json` |
| T6 | Static site build (`docs/`) + link/integrity checker | unclaimed | — | `tools/`, `docs/`, workflows |
| T7 | Integration: merge, re-verify combined data, publish, PR + merge | unclaimed | — | `main` (via PR) |

## Log

### 2026-10-21 — S-20261021-A — T1 done
- Repo at `96f089b` contained only a 7-byte `README.md`. No prior data, no site, no CI.
- Created layout: `data/` (JSON + schema), `tools/` (harvest/build/verify), `docs/` (site).
- Evidence: `git log --oneline` → single commit "Initial commit"; `ls -la` → `README.md` only.
- Irregularity: repository had no `.gitignore`, no license, no Pages config — logged for review.

### 2026-10-21 — S-20261021-A — T2 claimed, in progress
- Method constraint (verified, not assumed): the sandbox HTTP client can only reach
  `github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`,
  `pypi.org`, `files.pythonhosted.org`. Direct `curl https://www.olbg.com/` returned
  `SSL_ERROR_SYSCALL` (exit 35) for OLBG, ESPN and BBC alike.
- Therefore OLBG pages were retrieved with the agent's page-retrieval tool and parsed by
  hand, with the retrieval timestamp and verbatim URL recorded per row in
  `data/matches.json`. No value is inferred: anything the page did not state is left
  blank and logged in `data/flagged.json`.
- Sport taxonomy taken verbatim from the OLBG "Betting Tips by Sport" list
  (https://www.olbg.com/betting-tips, retrieved 2026-10-21), which exposes sport IDs:
  Football/1, Horse_Racing/2, Tennis/3, Basketball/4, Golf/5, Cricket/7, Snooker/8,
  Rugby_Union/9, Rugby_League/10, American_Football/11, Baseball/12, Ice_Hockey/13,
  Motor_Racing/14, Darts/15, Boxing/16, Cycling/17, Handball/20, Volleyball/21,
  Gaelic_Football/25, Hurling/26, Greyhounds/28.
