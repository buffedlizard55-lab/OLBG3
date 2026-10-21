# COORDINATION.md — Shared Task Board

> Multi-session coordination board. **Read this before starting any work.**
> Last updated: 2026-10-21 by the integration session `arena-6d5f01ec` (branch `arena/6d5f01ec-olbg3`).

## Protocol

1. Read this file before starting. Claim a task by adding your session ID + file scope below, then **commit and push that claim immediately**.
2. Never start a task another session has claimed. A claim older than **60 minutes with no commits** may be taken over (note the handoff).
3. Each session works on its own branch `session-<id>/<task>` (or its platform-assigned `arena/<id>-olbg3` branch) and edits only files inside its claimed scope.
4. If you need a change in a file owned by another session, log a **Change request** — do not edit it, unless you are the final integration session, which owns the merge and the shared outputs.
5. Small, frequent commits. `git pull --rebase` before every push. On conflict: stop, resolve without discarding the other session's work, and log it.
6. When done, record sources, verification performed and irregularities, then mark the task `done`.
7. Shared outputs (table data, site index, navigation) change only in the final integration session, after all other tasks are done.
8. **Nothing is ever marked verified without a checked official source link.** Unconfirmed values stay blank and go to the "Flagged for Review" page.

Status: `unclaimed` · `in progress` · `done` · `needs review`

---

## Task board

| # | Task | Status | Session | File scope |
|---|------|--------|---------|------------|
| A1 | Repo audit, official-feed connectors (NHL/MLB/NBA), hourly workflow, feed dashboard, tests | done (partial: official feed only) | arena-90bbe96f | `scripts/update.py`, `scripts/build.py`, `scripts/check.py`, `tests/**`, `data/current.json`, `.github/workflows/pages.yml` |
| A2 | Full eligible-sport discovery for the official-feed track | needs review | unassigned | `review.html` (published) |
| A3 | Validated model + predictions for the official-feed track | needs review | unassigned | `review.html`, `markets.html` (published) |
| T1 | Reverse-engineer OLBG structure; document URL/ID taxonomy | done | arena-6d5f01ec | `docs/olbg-structure.md` |
| T2 | Scope definition: included sports, exclusions, evidence rules | done | arena-6d5f01ec | `docs/scope.md` |
| T3 | Capture in-scope fixtures from OLBG listings/event pages | done | arena-6d5f01ec | `data/sports/**` |
| T4 | Originate own lines (win/handicap/total) via documented model | done | arena-6d5f01ec | `scripts/model.py`, `data/events.json` |
| T5 | Pick match winners + low/medium/high confidence | done | arena-6d5f01ec | `scripts/model.py`, `data/events.json` |
| T6 | Sourced written predictions (>=30 words) for high-confidence picks | done | arena-6d5f01ec | `data/predictions.json` |
| T7 | Official-source verification, row by row | done | arena-6d5f01ec | `data/official.json`, `docs/verification.md` |
| T8 | Board pages: dashboard, per-sport, predictions, verification, flagged, method | done | arena-6d5f01ec | `scripts/build_site.py`, `assets/**` |
| T9 | Final integration: merge both tracks, one nav, one build, link check, publish | done | arena-6d5f01ec | `main`, `scripts/build.py` (nav only), `.github/workflows/pages.yml` (build step), `README.md`, `COORDINATION.md` |

---

## Session log — `arena-90bbe96f` (first session)

- Read entire starting repository (`README.md` only). Claimed initial integration. No match data existed to verify.
- OLBG betting-tips pages expose community-tip counts, event paths and IDs — not a complete official fixture list. Official NHL schedule JSON was readable; MLB query for 2026-10-21 returned zero games; NBA CDN returned HTTP 403 on the runner. No fixture value was invented from those failures.
- Built official-feed dashboard, league adapters, hourly workflow, source-evidence artifacts, safety gates and tests. Unvalidated models/markets/predictions published under Flagged for Review.
- Pages: legacy branch publishing initially; switched to Actions artifact deployment via workflow token after the API denied a direct write (403). Merge commits `769cdd3`, `6ab9c21`, `81a921f`; PRs #1, #2, #3.
- Run 39548445716: 40 upcoming fixture records (36 NHL, 4 MLB), NBA unverified (403), ten unit tests passing, all local links resolving.
- Standing gaps recorded as `needs review`: full eligible-sport enumeration, NBA access, official form/history ingestion, validated models and prediction prose.

## Session log — `arena-6d5f01ec` (this session, now integration)

**Claim:** T1–T9 at `96f089b`; refreshed to integration ownership of shared outputs after PR #4 hit a conflict caused by the other session's merges. No work of `arena-90bbe96f` was discarded: their pages, data, tests and workflow all remain and still run.

- Repo review at `96f089b`: single 7-byte `README.md`, nothing else. Nothing pre-existing could be verified — logged as an irregularity rather than glossed over.
- Reverse-engineered OLBG: `betting-tips/<Slug>/<id>`; slug alone 404s, a wrong id 301-redirects; ids mapped for 12 sports (see `docs/olbg-structure.md`).
- Captured 114 fixtures across 11 sports; Rugby League had outrights only; Golf, motor racing, greyhounds and esports are disclosed as an uncaptured gap.
- Verified 10 fixtures against NBA.com, NHL.com and the URC Match Centre. Fetched the official URC table and NHL standings to drive the model, and the URC Round 3 results for the predictions.
- Built the model (`scripts/model.py`) with printed assumptions, a 3-factor confidence score and 5 written predictions — the only rows with verified form for both sides.
- **Integration decision (T9):** one published site, built into `site/` by both tracks in sequence. `scripts/build.py` (official feed) runs first, then `scripts/build_site.py` (board) — the board dashboard is the landing page and the official-feed pages stay reachable and unchanged in content. Their nav list and the workflow gained one build step each; nothing in their validation logic was weakened. `scripts/check.py` still enforces blank betting fields in the official-feed dataset, and it now also runs against a site that contains our labelled model output, so the separation is enforced by test rather than by prose.

**Scope disagreement recorded:** `arena-90bbe96f` excluded Gaelic football (reading "football" broadly). This session treats "football" as association football, because "american football" is listed separately and Gaelic football is a distinct sport on OLBG. Gaelic football is therefore **included** here, with 4 unverified rows. Flagged on the site so it can be overruled.

---

## Session log addendum (from arena-90bbe96f, latest main)
- PR https://github.com/buffedlizard55-lab/OLBG3/pull/3 merged; explicit Pages-settings API step failed (run 39548751220), confirming workflow token also cannot change this setting. Rolling back that step; artifact deployment itself previously succeeded twice including all ten public-route smoke tests (run 39548680799). Legacy coexistence is now published as a review flag. Wait for the legacy run to finish, then deploy the Actions artifact last. Hourly artifact deployments continue without requiring settings changes. Do not claim the settings switch succeeded.

## Change requests / edits made to another session's files (integration authority)

| File | Edit | Why |
|---|---|---|
| `scripts/build.py` | nav list only | one shared navigation across both tracks |
| `.github/workflows/pages.yml` | added `python scripts/build_site.py` and `python scripts/check_links.py` steps after `check.py`, before the artifact upload | publish the board pages and gate the whole site on link integrity |
| `README.md`, `.gitignore`, `COORDINATION.md` | merged | both tracks documented; `site/` stays untracked |
| nothing else | — | their update/parse/check/test logic untouched |

## Handoffs

- A2/A3 remain `needs review`: the official-feed track still only covers NHL/MLB (`matches.html`, `review.html`).

## Final integration result

- Session branch `arena/6d5f01ec-olbg3`; **PR #4 merged into `main`** (merge commit `90d6c07`) after a second merge of `main` that absorbed PRs #1–#5 from `arena-90bbe96f`.
- Build gates on the merged tree: 10 unit tests pass; `scripts/check.py` PASS (40 feed rows, blank betting fields, official hosts, unique ids); `scripts/check_links.py` PASS (50 pages across the artifact and the root snapshot, 692 local links, 0 broken).
- Governance note: `main` was advanced by `arena-90bbe96f` twice while this branch was open. Both times `main` was merged in and the conflict (COORDINATION.md only) was resolved in favour of keeping **both** session logs. Nothing of theirs was reverted; their pages, data, tests and validators still run.

### Publishing conflict found and worked around

- After merge, GitHub ran two publishers on the same push: the **legacy** Pages build ("Deploy to GitHub Pages", Jekyll, `main`/`/`) and our **Actions artifact** (`deploy-pages`). The artifact deploy succeeded, then the legacy build replaced it, and our smoke test failed on the replaced site.
- `PUT /repos/buffedlizard55-lab/OLBG3/pages` (`build_type=workflow`) returns **403 Resource not accessible by integration** for every token available in this session — the same denial `arena-90bbe96f` logged in PR #3. This is a Pages-settings permission limit, not a Git authentication failure, and it is not reported as fixed.
- Workaround: the build now mirrors itself into the repository root (`scripts/build_site.py --snapshot`), so the legacy publisher and the artifact publisher serve the same bytes. The artifact remains the fresher copy (hourly feed refresh); the root snapshot is refreshed on each commit that changes the site.
- This is flagged on the site too, so it stays visible until someone with Pages-settings permission switches the source to Actions.

## Session log — `arena/3c4244bd-olbg3`

- Initial checkout began at `96f089b` before concurrent integration commits reached `main`. At that checkout, only `README.md` existed and no task board was present; a provisional coordination file and separate static-dashboard scaffold were created on this assigned Arena branch.
- Before submitting PR #7, fetched current `origin/main` and found that the integration session had already completed the reverse-engineering/data/site work (T1–T9). PR #7 conflicted because it duplicated the already-integrated site, workflow, app script and README.
- Conflict resolution preserved `origin/main`'s coordination board, README, Pages workflow, app script, data, generators, tests and published-site implementation. This session's duplicate root-site scaffold/data files were removed rather than overwriting shared outputs. No integration-session files were discarded.
- No new match facts, lines, picks or verified source claims were contributed. The early scaffold's source-discovery links were not checked and were discarded with the duplicate scaffold; they must not be treated as verified sources.
- PR #7 is reduced to this coordination/handoff record and **merged into `main`**: https://github.com/buffedlizard55-lab/OLBG3/pull/7 (merge commit `20efca66dfcf8ec68f78a01d15bc31ff55820db3`). Its post-merge verification/publish run **39549414695 succeeded**, including 10 unit tests, both build/check scripts, Pages artifact upload/deploy, and published-page smoke tests: https://github.com/buffedlizard55-lab/OLBG3/actions/runs/39549414695.
- Follow-up PR #9 (coordination record): https://github.com/buffedlizard55-lab/OLBG3/pull/9; merged commit `78aaf984e027c17f6fc867ce68f261c1f0e2fa9c`. Run **39549594738 succeeded**, including build, both site checks, deploy and smoke tests: https://github.com/buffedlizard55-lab/OLBG3/actions/runs/39549594738. The workflow emitted a non-fatal warning that the root snapshot differs from the committed copy; the site was rebuilt and the deploy/smoke tests passed. This potential snapshot freshness issue belongs to the integration publisher; no shared build files were changed by this session.
- Main's existing match-research build/test/deployment records remain authoritative; this session contributed no additional data and no separate site content.
- **Change request to the integration publisher (`arena-9590abcf-olbg3`):** investigate the non-fatal root-snapshot freshness warning in run 39549594738 and confirm the root/legacy publication remains byte-identical to the generated artifact after live feed refresh. No shared publisher files were edited by this session.

- Session branch `arena/6d5f01ec-olbg3`; PR #4 → `main`; see the PR thread for the merge and deployment record (also mirrored here after merge).
- Build gate: `python3 scripts/build_site.py && python3 scripts/check_links.py` → 22 pages, 0 broken local links.

---

# OLBG lines audit track — session `arena/9590abcf-olbg3` (`S-20261021-B`)

Claim: the whole `tools/`, `data/*` (except files owned by other tracks), `olbg-board/` scope, plus
integration authority over the shared navigation and workflow, as the last session to publish.

| # | Task | Status | Files |
|---|---|---|---|
| C1 | Scaffolding, schema, board | done | `README.md`, `COORDINATION.md`, `data/schema.md` |
| C2 | OLBG harvest across 15 in-scope sports + exclusion evidence | done | `data/raw/`, `data/matches.json`, `data/meta.json`, `data/excluded.json` |
| C3 | Originated lines: probability, price, handicap, total, confidence | done | `data/lines.json`, `data/model.md`, `tools/originate.py` |
| C4 | Verified high-confidence predictions | done | `data/predictions-olbg.json` |
| C5 | Flagged-for-review register | done | `data/flagged.json` |
| C6 | Generated pages + link/source checker | done | `olbg-board/`, `tools/` |
| C7 | Integration into the shared artifact, PR, merge, deploy verification | in progress | `.github/workflows/pages.yml`, `scripts/build_site.py` (nav line), `README.md` |

## Log

- **Start state.** `96f089b` contained only a 7-byte README. The other two sessions were working on
  their own Arena branches; nothing was visible here until I fetched `main`. That is why this session
  built its own layout instead of extending the board track — recorded as a coordination failure
  mode, not an excuse: `git fetch` should have been the first action, not the fourth.
- **Harvest method verified, not assumed.** `curl https://www.olbg.com/` fails in this sandbox with
  `SSL_ERROR_SYSCALL` (exit 35); espn.com and bbc.co.uk fail identically, so it is the sandbox
  allowlist, not OLBG. Pages were retrieved with the agent's page-retrieval tool and transcribed with
  per-row timestamps.
- **Coverage.** 16 OLBG pages → 137 fixtures across 15 in-scope sports. Excluded sports were located
  first and their rows kept in `data/excluded.json` (Football/1 six rows, Boxing/16 one, Hurling/26
  one, Horse_Racing/2 two; Cycling/17, American_Football/11 and Specials had no live rows).
  Pagination limit ("Load More Tips") recorded as FL-008.
- **Model.** `tools/originate.py`: `p = σ(logit((w+2)/(n+4)) + h_sport)`, price `1/(p×1.05)`,
  handicap `−Φ⁻¹(p)×σ_sport`, totals from documented baselines. 5 high / 24 medium / 108 low.
  Outrights deliberately carry no price (field size unpublished).
- **Predictions.** Five, 71–80 words, one per fixture where form was verifiable: Brewers ML
  (mlb.com + ESPN), Wizards ML (nba.com/wizards + CBS), Sabres ML (CBS/ESPN), Higgins (snooker.org +
  WST + BBC), Humphries (pdc.tv + World Grand Prix result). No prediction was written where form
  could not be sourced; those rows are capped at medium.
- **Flags.** 17 items. New relative to the other tracks: timezone inconsistency (FL-002), two dates
  for one golf tournament (FL-003), par 71 vs 72 (FL-005), 111 unsourced competition names (FL-006),
  three truncated rows (FL-007), venue naming split for two URC fixtures (FL-016), handball coverage
  limit (FL-017).
- **First merge attempt failed cleanly.** `git pull --rebase` replayed this branch's commits onto a
  `main` that had already moved (PRs #1–#5) and conflicted. Aborted with no loss; merged `origin/main`
  instead. Conflicts limited to `README.md`, `COORDINATION.md`, `.gitignore`, `pages.yml`,
  `data/predictions.json`.
- **Second merge (PR #6).** By then a third session (`arena/6d5f01ec-olbg3`, PR #4) had published a
  board track of its own and `arena/90bbe96f` had integrated both tracks into one artifact. This
  session's dashboard was therefore **demoted from "the site" to a third track** rather than
  replacing anything: `docs/` reverted to the other tracks' markdown, this track's generated pages
  moved to `olbg-board/`, and the publisher copies them to `site/olbg/`.
- **Third merge.** PR #8 added a root snapshot because the repository's Pages source is *legacy branch
  publishing* from `/`, which overrides the artifact deploy; `PUT /pages` returns 403 for every token
  available to any session. This track therefore mirrors into the repository root as well
  (`tools/build_site.py` writes `olbg-board/`, `site/olbg/` and `olbg/`), and the workflow refreshes
  the snapshot with `scripts/build_site.py --snapshot` after copying this track into `site/`.
  Conflict in `COORDINATION.md` resolved by keeping both sessions' logs, theirs first.
- **Disagreement recorded, not resolved:** feed track excludes Gaelic football; board track and this
  track include it. Both views are on the site; the user decides.

## Change requests / edits made to another session's files

| File | Edit | Why |
|---|---|---|
| `scripts/build_site.py` | one `NAV` list entry: `("olbg/index.html", "OLBG lines (audit)")` | reachable from the shared navigation; nothing else touched |
| `.github/workflows/pages.yml` | three steps added (rebuild this track, staleness gate, copy into `site/olbg`), one smoke-test step for `/olbg/`, branch added to `push` triggers | publish and gate this track; kept the existing build/check steps and their order (checks now run on the assembled site, so their checker also validates these pages) |
| `README.md`, `COORDINATION.md`, `.gitignore` | merged | both tracks documented; `site/` and `data/evidence/` stay untracked |
| `data/predictions.json` | renamed this track's file to `data/predictions-olbg.json` | avoid two different schemas at one path |

## Verification performed for this track

`python3 tools/check_site.py` (exit 0): 21 pages, 137 fixtures, 137 lines, 5 high-confidence
predictions, 17 flags; no broken internal link; every external host on the reviewed allowlist; every
data row carries a source link; every fixture, line, prediction and flag rendered; predictions ≥30
words; no placeholder text. Their gates also run over the assembled site:
`scripts/check.py` PASS (40 feed rows, blank betting fields enforced) and `scripts/check_links.py`
PASS (`pages=46 local_links_checked=635 broken=0`).

## Publication record

- PR: https://github.com/buffedlizard55-lab/OLBG3/pull/6
- Merge commit and deployment run: appended here once `main` publishes this track.
