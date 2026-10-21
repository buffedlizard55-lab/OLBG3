# Unreferenced alternative sport boards (kept for review)

`../../sports/*.json` is the schema the publisher (`scripts/build_site.py`) reads:
`{sport, olbg_slug, olbg_id, listing_url, fetched, listing_note, events[]}`.

On 2026-10-21 `main` carried unresolved merge-conflict markers in ten of those files. One side was the
publisher schema above, the other was a per-event board (a top-level list of events with
`originated_markets`, `predicted_winner`, `confidence_level`, `prediction_text`). The markers broke
`json.load`, so the Pages job failed on every push and the site stopped updating.

The publisher schema was kept because the code reads it. The other side is copied here unchanged so
nothing produced by the session that wrote it is lost. Nothing in this directory is read by any
script, and both tracks already publish originated lines and predictions for these sports, so it is a
reference copy only. Delete it once someone has compared the two.

`golf.json` and `motor_racing.json` were also in the per-event list schema, with no counterpart in the
publisher schema, so they moved here too rather than being rewritten into a shape their author did not
choose. Those two sports are covered by the OLBG audit track (`/olbg/sports/golf.html`,
`/olbg/sports/motor-racing.html`), which is generated from `data/raw/olbg-harvest-20261021.tsv`.
