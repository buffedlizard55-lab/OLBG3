# OLBG Sports Analytics & Line Origination Platform

A high-performance analytics, proprietary line origination, and match prediction platform built from the ground up by reverse-engineering [OLBG.com](https://www.olbg.com).

## 🚀 Live GitHub Pages Deployment
- **Live Site:** [https://buffedlizard55-lab.github.io/OLBG3/](https://buffedlizard55-lab.github.io/OLBG3/)
- **Flagged for Review Registry:** [https://buffedlizard55-lab.github.io/OLBG3/flagged-review.html](https://buffedlizard55-lab.github.io/OLBG3/flagged-review.html)
- **Methodology Documentation:** [https://buffedlizard55-lab.github.io/OLBG3/methodology.html](https://buffedlizard55-lab.github.io/OLBG3/methodology.html)
- **Audit Track:** [https://buffedlizard55-lab.github.io/OLBG3/olbg/index.html](https://buffedlizard55-lab.github.io/OLBG3/olbg/index.html)

---

## 📌 Project Overview & Scope
The platform monitors and extracts all upcoming sports events from OLBG across **12 non-excluded sports**, while strictly filtering out excluded categories (*soccer, football, boxing, ufc, mma, american football, hurling, horse racing, cycling, and entertainment/political specials*):

1. **Basketball** (NBA, EuroLeague, EuroCup, Basketball Champions League, Korea KBL)
2. **Baseball** (MLB)
3. **Tennis** (ATP & WTA Tour, Challenger series)
4. **Cricket** (One Day Internationals, T20 Internationals, CSA T20 Challenge)
5. **Ice Hockey** (NHL, Austrian ICE EHL, Swedish Hockey League)
6. **Darts** (PDC European Championship)
7. **Snooker** (World Snooker Tour - Northern Ireland Open)
8. **Handball** (EHF Champions League, Denmark Handboldligaen)
9. **Volleyball** (Poland PlusLiga, Germany 1. Bundesliga, Italy Serie A1)
10. **Rugby Union** (United Rugby Championship, France Top 14, France Pro D2)
11. **Motor Racing** (Formula 1 World Championship - USA Grand Prix)
12. **Golf** (PGA Tour, DP World Tour, LPGA Tour)

---

## 🎯 Key Features

### 1. Proprietary Line Origination
- **Moneyline (Fair Win Odds):** True probabilities calculated by stripping out synthetic bookmaker overrounds and vigorish.
- **Handicap / Point Spread / Run Line / Puck Line:** Model-derived point/run/goal spread thresholds based on team efficiency ratings and home-field advantage.
- **Game Totals:** Expected scorelines originated from pace and offensive/defensive ratings.

### 2. Match Winner Selections & Confidence Tiers
Every fixture is analyzed to designate a predicted match winner and categorized into one of three confidence tiers:
- **High Confidence (&ge; 65% probability / structural edge):** Accompanied by verified, human-written predictions (&ge; 30 words each) incorporating team form, individual player stats, head-to-head history, and unambiguous betting selections.
- **Medium Confidence (54% &ndash; 64%):** Solid statistical edges based on primary indicators.
- **Low Confidence (&lt; 54%):** Contests with high variance or tactical coin-flips.

### 3. Line-by-Line Verification & Source Attribution
- Every row links directly to an **official governing body site** (e.g., `NBA.com`, `MLB.com`, `ATPTour.com`, `WTATennis.com`, `ICC-cricket.com`, `NHL.com`, `PDC.tv`, `WST.tv`, `Eurohandball.com`, `PlusLiga.pl`, `LNR.fr`, `Formula1.com`, `PGATour.com`).
- Discrepancies, community tipster hallucinations, or calendar mismatches are flagged in the **Flagged for Review** registry (`flagged-review.html`).

---

## 📂 Repository Directory Structure
```
├── COORDINATION.md             # Multi-session coordination board & audit log
├── README.md                   # Project documentation & operational summary
├── build_full_database.py      # Complete 76-fixture database builder
├── build_site.py               # Static site HTML, CSS, JS generator
├── index.html                  # Master Dashboard interface
├── flagged-review.html         # Flagged for Review register
├── methodology.html            # Mathematical modeling & origination methodology
├── css/
│   └── styles.css              # Modern responsive styling
├── js/
│   └── dashboard.js            # Client-side filtering, searching & analysis modal
├── sports/                     # Category subpages (12 non-excluded sports)
│   ├── basketball.html
│   ├── baseball.html
│   ├── tennis.html
│   ├── cricket.html
│   ├── ice-hockey.html
│   ├── darts.html
│   ├── snooker.html
│   ├── handball.html
│   ├── volleyball.html
│   ├── rugby-union.html
│   ├── motor-racing.html
│   └── golf.html
└── data/
    ├── master_matches.json     # Complete structured database
    ├── flagged_review.json     # Flagged review entries
    └── sports/                 # Sport-specific JSON datasets
```

---

## 🛠️ Verification & Build Commands
To regenerate the dataset and re-compile the site:
```bash
python3 build_full_database.py
python3 build_site.py
```

To test locally:
```bash
python3 -m http.server 8000
```
