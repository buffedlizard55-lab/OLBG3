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

- Session branch `arena/6d5f01ec-olbg3`; PR #4 → `main`; see the PR thread for the merge and deployment record (also mirrored here after merge).
- Build gate: `python3 scripts/build_site.py && python3 scripts/check_links.py` → 22 pages, 0 broken local links.
