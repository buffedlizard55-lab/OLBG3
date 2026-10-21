# OLBG Research Desk

A static, source-first dashboard scaffold for organizing non-excluded sports fixtures, independently originated betting lines, market assessments, confidence picks, and review flags. It is designed for GitHub Pages and uses plain HTML, CSS, JavaScript, and JSON.

## Important verification status

The initial repository had no fixture or research data. In this session, the live OLBG website and official sports schedules could not be accessed: network access was restricted to GitHub and package-registry hosts. Consequently, **no current match, event date, recent form, result, market line, injury, pick, or prediction has been independently verified or published**. The dashboard intentionally displays zero verified records rather than filling gaps with guesses.

The category list in `data/sports.json` is provisional. Its organization URLs are source-discovery starting points only, not match-level citations or claims that the current pages were checked. See the dashboard's **Flagged for Review** section for all known limitations.

## Local preview

From the repository root, run any static web server, for example:

```sh
python3 -m http.server 8000
```

Open `http://localhost:8000`. On GitHub Pages, the root `index.html` is the landing page and `sports.html?category=<id>` provides category detail pages. The category filter and table read from `data/matches.json`.

## Data contract

- Every match record must include a direct, official, match-specific `matchSourceUrl`.
- Keep fields blank when not confirmed. Do not use bookmaker pages or inference as substitutes for an official fixture fact.
- Keep originated prices/lines separate from market prices, with methodology, evidence and timestamps.
- Each market record should include market name, our line/price, selection, rationale, direct source URLs, and verification time.
- A confidence label is one of `low`, `medium`, or `high`; it is an analytical judgment and must be supported by evidence, not presented as a verified fact.
- High-confidence prediction copy must be unique, at least 30 words, and explicitly state the selection. Form, recent history and other factual details need official supporting links.
- Add any missing, inaccessible, conflicting, or unverified facts to **Flagged for Review**; never silently fill them.

The schema and empty data state are in `data/matches.json`. Official source discovery links by provisional sport are in `data/sports.json`.

## Pages workflow

`.github/workflows/pages.yml` deploys this static site to GitHub Pages on pushes to `main` and on manual workflow dispatch. The repository's Pages setting must allow GitHub Actions deployments. A successful branch push alone does not confirm a live deployment.
