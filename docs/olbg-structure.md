# OLBG.com — reverse-engineered structure

Captured 2026-10-21 by reading live pages (no API key, no scraping behind a login).

## URL grammar

```
listing : https://www.olbg.com/betting-tips/<Sport_Slug>/<sport_id>
event   : https://www.olbg.com/betting-tips/<Sport>/<Group>/<Competition>/<Home>_v_<Away>/<sport_id>?event_id=<id>
```

* `Sport_Slug` is authoritative. `/betting-tips/Cricket` (no id) → **404**. `/betting-tips/Basketball` → **404**.
* A wrong id does not 404 — it 301-redirects to the correct slug+id. Observed: `Ice_Hockey/11` → `13`, `Baseball/5` → `12`, `Handball/14` → `20`.
* `Group` is a coarse bucket: `NBA`, `NHL`, `MLB`, `European`, `Other`, or `All_<Sport>` when OLBG is not publishing a competition.
* `Competition` is the league *when OLBG knows it*; otherwise `All_Events`. That is why competition is blank on several sports.

## Sport ids found

| Sport | id | Listing |
|---|---|---|
| Tennis | 3 | /betting-tips/Tennis/3 |
| Basketball | 4 | /betting-tips/Basketball/4 |
| Cricket | 7 | /betting-tips/Cricket/7 |
| Snooker | 8 | /betting-tips/Snooker/8 |
| Rugby Union | 9 | /betting-tips/Rugby_Union/9 |
| Rugby League | 10 | /betting-tips/Rugby_League/10 |
| Baseball | 12 | /betting-tips/Baseball/12 |
| Ice Hockey | 13 | /betting-tips/Ice_Hockey/13 |
| Darts | 15 | /betting-tips/Darts/15 |
| Handball | 20 | /betting-tips/Handball/20 |
| Volleyball | 21 | /betting-tips/Volleyball/21 |
| Gaelic Football | 25 | /betting-tips/Gaelic_Football/25 |
| Hurling (excluded) | 26 | /betting-tips/Hurling/26 |

Other referenced ids: Football 1, Horse Racing 2, Golf, Motor Racing, Greyhounds, American Football, Boxing — present on the all-sports page.

## What a listing row exposes

1. Event link (contains group/competition/slug and `event_id`)
2. Date + time (`Today 19:10`, `23 Oct 12:00`, `Tomorrow 03:00`) — **no time zone stated**
3. Competition name (only for some sports)
4. The market (`Money Line`, `Win Match`, `To Win`, `Handicap`, `Game Totals`, `Total Legs`, `Set Betting`, `Set Score`, `Puck Line`)
5. The most-tipped selection
6. `n/m Win Tips` and the percentage of tips on that selection
7. Optional: number of comments, "1 expert" badge

## Quirks that affect data quality

* **Start times run late.** NHL shows 19:37 where NHL.com says 19:30 EDT; NBA shows 19:10/19:40/20:10 where NBA.com says 19:00/19:30/20:00 ET. Consistent 7–10 minute offset.
* **Time zone is undisclosed.** Times align with US Eastern for North American sport and with UK/local time for URC fixtures. Never convert them; publish verbatim.
* **Pagination.** `Load More Tips` truncates baseball, ice hockey, snooker, Gaelic football, handball, darts.
* **Outrights are mixed in** (World Cup 2027, Big Bash, State of Origin 2027, Super League 2027). They are not fixtures and are excluded from the match board.
* **Rugby League** had only outright markets at capture time — zero fixtures.
* **Gaelic football** rows carry no market label at all on OLBG's own page, yet the selection is handicap-styled (`Nemo Rangers +1.50`).
