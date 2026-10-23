#!/usr/bin/env python3
"""brief_coverage.py - accounting for what the brief asks for versus what the board publishes.

The brief asks for the five highest-confidence picks for every covered sport, every day, on
matches priced between -250 and +10000 US odds (decimal 1.40 to 101.00), each with a written
prediction of at least 30 words. This script does not grade anything. It only counts what is
already published on the two independent tracks and states, from those same rows, the mechanical
reason a sport falls short of five live HIGH picks. Nothing is inferred and no source is fetched.

Inputs (all committed, no network):
  data/events.json        root board rows incl. model prices, verification and release decisions
  data/lines.json         /olbg/ audit-track lines incl. release decisions
  data/matches.json       /olbg/ fixtures (sport naming)
  data/meta.json          scope: allowed sports and the verbatim exclusion list

Output:
  data/brief_coverage.json  consumed by scripts/build_site.py, validated by scripts/check_board.py
"""
import json
import statistics
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

from release import OFFICIAL_CLOCK_HOSTS

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / 'data'

TARGET_PER_SPORT = 5          # the brief: five highest-confidence picks per covered sport, daily
BAND = '-250 to +10000 US (decimal 1.40 to 101.00)'


def load(name):
    return json.loads((D / name).read_text())


def host(url):
    try:
        return (urlparse(url).hostname or '').lower()
    except (TypeError, ValueError):
        return ''


def official_hosts(root_rows, verifications):
    """Hosts already recorded in this repo as governing-body / club-official sources.

    This is a provenance boundary, not a claim that a page still says what it said: nothing is
    fetched here. It only separates 'the competition's own site' from 'a media report'.
    """
    hosts = set(OFFICIAL_CLOCK_HOSTS)
    for r in root_rows:
        v = r.get('verification') or {}
        if v.get('status') in ('verified', 'corroborated'):
            h = host(v.get('official_url'))
            if h:
                hosts.add(h)
    for entry in (verifications.get('event_verifications') or {}).values():
        for key in ('official_url', 'source', 'url'):
            h = host(entry.get(key) if isinstance(entry, dict) else None)
            if h:
                hosts.add(h)
    return hosts


def prose_evidence(preds, off_hosts):
    """Count how the written pieces are evidenced, from their own `sources` lists."""
    if not preds:
        return {'pieces': 0, 'high': 0, 'words_min': None, 'words_median': None,
                'words_max': None, 'under_30_words': 0, 'citing_an_official_host': 0,
                'citing_only_hosts_outside_official_set': 0, 'hosts_outside_official_set': {}, 'duplicate_bodies': 0,
                'withheld_bodies': 0}
    words, third, cite, only_third, seen, dup, withheld = [], Counter(), 0, 0, set(), 0, 0
    for p in preds:
        body = p.get('text') or p.get('body') or ''
        if not body.strip():
            withheld += 1
            continue
        words.append(len(body.split()))
        norm = ' '.join(body.split()).lower()
        if norm in seen:
            dup += 1
        seen.add(norm)
        hostlist = [host(s.get('url')) for s in p.get('sources', []) if s.get('url')]
        if any(h in off_hosts for h in hostlist):
            cite += 1
        elif hostlist:
            only_third += 1
        for h in hostlist:
            if h and h not in off_hosts and h != 'www.olbg.com':
                third[h] += 1
    return {
        'pieces': len(preds),
        'high': sum(1 for p in preds if p.get('status') in ('high',)),
        'words_min': min(words) if words else None,
        'words_median': (statistics.median(words) if words else None),
        'words_max': max(words) if words else None,
        'under_30_words': sum(1 for w in words if w < 30),
        'citing_an_official_host': cite,
        'citing_only_hosts_outside_official_set': only_third,
        'hosts_outside_official_set': dict(sorted(third.items())),
        'duplicate_bodies': dup,
        'withheld_bodies': withheld,
    }


def markets(model):
    prices = model.get('prices') or {}
    return {
        'win': bool(prices.get('win_home') or prices.get('win_away')),
        'outright': bool(prices.get('single')),
        'handicap': bool(model.get('handicap')),
        'total': bool(model.get('total')),
    }


def build():
    events_doc = load('events.json')
    events = events_doc['events']
    gap = [dict(r) for r in load('gap_sports.json')['rows']]
    for r in gap:
        r.setdefault('market_type', 'outright_or_race')
    lines = load('lines.json')
    matches_doc = load('matches.json')
    matches = {m['id']: m for m in (matches_doc['matches'] if isinstance(matches_doc, dict) else matches_doc)}
    meta = load('meta.json')

    allowed = [k.replace('_', ' ') for k in meta['allowed_sports_olbg_ids']]
    excluded = meta['excluded_sports_verbatim']

    # ---- root board, per sport -------------------------------------------------------------
    root_by_sport = {}
    for r in events + gap:
        root_by_sport.setdefault(r['sport'], []).append(r)

    # ---- /olbg/ audit track, per sport -----------------------------------------------------
    ol_by_sport = {}
    for line in lines:
        sport = matches[line['match_id']]['sport']
        ol_by_sport.setdefault(sport, []).append(line)

    # ---- live HIGH picks, union by OLBG event id -------------------------------------------
    # A fixture can be HIGH on both tracks. It is one match, not two, so the union de-duplicates
    # on the OLBG event id rather than adding the tracks together.
    union = {}
    for r in events + gap:
        if r['pick'].get('confidence') == 'HIGH':
            union[str(r.get('olbg_event_id'))] = {
                'event_id': str(r.get('olbg_event_id')), 'sport': r['sport'], 'tracks': ['root'],
                'root_ref': r['ref'], 'olbg_ref': None,
                'selection': r['pick'].get('label'), 'price': r['pick'].get('price'),
                'american': r['pick'].get('american'),
            }
    for line in lines:
        if line.get('confidence') != 'high':
            continue
        eid = line['match_id'].split('-', 1)[1]
        if eid in union:
            union[eid]['tracks'].append('olbg')
            union[eid]['olbg_ref'] = line['match_id']
        else:
            union[eid] = {
                'event_id': eid, 'sport': matches[line['match_id']]['sport'], 'tracks': ['olbg'],
                'root_ref': None, 'olbg_ref': line['match_id'],
                'selection': line.get('our_pick'), 'price': line.get('our_price_pick'),
                'american': line.get('our_us_odds_pick'),
            }

    sports = []
    for sport in allowed:
        root_rows = root_by_sport.get(sport, [])
        ol_rows = ol_by_sport.get(sport, [])
        root_high = [r for r in root_rows if r['pick'].get('confidence') == 'HIGH']
        ol_high = [l for l in ol_rows if l.get('confidence') == 'high']
        live = [u for u in union.values() if u['sport'] == sport]

        # mechanical reasons, each counted from published fields only
        no_form = sum(1 for r in root_rows
                      if (r['pick'].get('factors') or {}).get('official_form') == 0
                      and r['pick'].get('confidence') != 'HIGH')
        band_blocked = sum(1 for r in root_rows
                           if r['pick'].get('evidence_grade') == 'HIGH'
                           and not r['pick'].get('in_band')
                           and r['pick'].get('confidence') != 'HIGH')
        start_blocked = sum(1 for r in root_rows
                            if r['pick'].get('confidence') != 'HIGH'
                            and (r['pick'].get('kickoff_passed')
                                 or r['pick'].get('kickoff_started')
                                 or (r['pick'].get('release') or {}).get('status') not in (None, 'upcoming')))
        unpriced = sum(1 for r in root_rows if not (r['model'].get('prices') or {}))
        unverified = sum(1 for r in root_rows if r['verification']['status'] != 'verified')
        verified = sum(1 for r in root_rows if r['verification']['status'] == 'verified')

        mk = Counter()
        for r in root_rows:
            for key, present in markets(r['model']).items():
                if present:
                    mk[key] += 1
        ol_mk = Counter()
        for l in ol_rows:
            if l.get('our_price_pick'):
                ol_mk['win'] += 1
            if l.get('our_handicap_line') is not None:
                ol_mk['handicap'] += 1
            if l.get('our_total_line') is not None:
                ol_mk['total'] += 1

        reasons = []
        if not root_rows and not ol_rows:
            reasons.append('No OLBG row was captured for this sport, so nothing could be verified, '
                           'priced or graded. The sport is listed because the brief covers it, not '
                           'because a fixture exists in the committed capture.')
        if no_form:
            reasons.append(f'{no_form} of {len(root_rows)} root rows have no official current-form '
                           'input for both sides, so the model cannot grade them above MEDIUM '
                           '(a HIGH grade requires official form plus a verified fixture plus a '
                           f'price inside {BAND}).')
        if band_blocked:
            reasons.append(f'{band_blocked} root row(s) had HIGH-grade evidence but an originated '
                           f'price outside {BAND}. They are published as MEDIUM with the reason, not '
                           'bent into the band.')
        if start_blocked:
            reasons.append(f'{start_blocked} root row(s) are not released as current picks because '
                           'the official start had passed, the start was unverified, or the source '
                           'observation was stale at the publication clock.')
        if unpriced:
            reasons.append(f'{unpriced} root row(s) carry no win price at all (no defensible '
                           'official baseline), so no pick could be priced.')
        if unverified:
            reasons.append(f'{unverified} root row(s) are unverified or corroborated only; they are '
                           'never graded HIGH.')

        shortfall = max(0, TARGET_PER_SPORT - len(live))
        if shortfall and not reasons:
            reasons.append(f'Only {len(root_rows)} root row(s) and {len(ol_rows)} /olbg/ row(s) were '
                           'captured for this sport in the committed snapshot, so five picks cannot '
                           'exist without more fixtures. No gate is being failed here; there is simply '
                           'nothing more to verify or price in the capture.')
        sports.append({
            'sport': sport,
            'root_rows': len(root_rows),
            'root_verified': verified,
            'root_unverified_or_corroborated': unverified,
            'root_priced_win': mk['win'],
            'root_outright': mk['outright'],
            'root_handicap': mk['handicap'],
            'root_total': mk['total'],
            'root_high': len(root_high),
            'olbg_rows': len(ol_rows),
            'olbg_priced_win': ol_mk['win'],
            'olbg_handicap': ol_mk['handicap'],
            'olbg_total': ol_mk['total'],
            'olbg_high': len(ol_high),
            'live_high_union': len(live),
            'target': TARGET_PER_SPORT,
            'shortfall': shortfall,
            'meets_target': shortfall == 0,
            'blocking': {
                'no_official_form': no_form,
                'high_evidence_out_of_band': band_blocked,
                'start_or_source_gate': start_blocked,
                'unpriced': unpriced,
                'unverified_or_corroborated': unverified,
            },
            'reasons': reasons,
            'live_picks': sorted(live, key=lambda u: (u['root_ref'] or '', u['olbg_ref'] or '')),
        })

    # ---- cross-track reconciliation --------------------------------------------------------
    root_by_eid = {str(r.get('olbg_event_id')): r for r in events}
    pairs, agree, disagree, missing = 0, 0, [], 0
    for line in lines:
        eid = line['match_id'].split('-', 1)[1]
        row = root_by_eid.get(eid)
        if not row:
            continue
        pairs += 1
        root_pick = (row['pick'].get('label') or '').strip()
        ol_pick = (line.get('our_pick') or '').strip()
        if not root_pick or not ol_pick:
            missing += 1  # one model withheld a selection (conflict/held); not a disagreement
            continue
        if root_pick.lower() == ol_pick.lower():
            agree += 1
            continue
        disagree.append({
            'event_id': eid,
            'sport': row['sport'],
            'match': f"{row['home']} v {row['away']}",
            'root_ref': row['ref'],
            'root_selection': root_pick,
            'root_price': row['pick'].get('price'),
            'root_american': row['pick'].get('american'),
            'root_prob': round(row['pick'].get('prob') or 0, 4),
            'root_confidence': row['pick'].get('confidence'),
            'root_start_status': (row['pick'].get('release') or {}).get('status'),
            'olbg_ref': line['match_id'],
            'olbg_selection': ol_pick,
            'olbg_price': line.get('our_price_pick'),
            'olbg_american': line.get('our_us_odds_pick'),
            'olbg_prob': round(line.get('our_pick_probability') or 0, 4),
            'olbg_confidence': line.get('confidence'),
            'olbg_start_status': (line.get('release') or {}).get('status'),
            'olbg_url': line.get('olbg_url'),
        })

    off_hosts = official_hosts(events + gap, load('verifications.json'))
    evidence = {
        'root': prose_evidence(load('predictions.json')['predictions'], off_hosts),
        'olbg': prose_evidence(load('predictions-olbg.json')['predictions'], off_hosts),
        'official_host_count': len(off_hosts),
        'note': ('Counted from each piece\'s own sources list. "Official host" means a host already '
                 'recorded in this repository as a governing-body, league or club source; every other '
                 'host is listed as third-party and is NOT treated as verification. No page was '
                 'fetched while producing these counts, so a third-party citation is unverified '
                 'here and is published on the review register instead of being called confirmed.'),
    }

    doc = {
        'description': (
            'What the brief asks for versus what is published. Counts are recomputed from the '
            'committed rows by scripts/brief_coverage.py; no fixture, price, grade or source is '
            'changed here. targets are the brief\'s, not a claim of achievement. A row can be '
            'short of HIGH for several reasons at once, so the blocking counts overlap.'
        ),
        'brief_target': {
            'picks_per_sport_per_day': TARGET_PER_SPORT,
            'price_band_us': BAND,
            'min_prediction_words': 30,
            'markets_to_investigate': ['win / money line', 'handicap / spread / puck line / run line',
                                       'match total over-under', 'outright / race / tournament'],
            'excluded_sports': excluded,
        },
        'source_clocks': {
            'root_publication_clock': events_doc.get('publication_clock'),
            'root_capture': events_doc.get('generated'),
            'root_built': events_doc.get('built'),
            'notes': ('The publication clock is the committed snapshot clock, not the wall clock at '
                      'build time. A pick whose official start has passed since that clock is expired '
                      'in the browser by assets/release.js. No source was re-verified by this script; '
                      'no checked_at or quote was renewed. This script fetches nothing: any clock,'
                      ' quote or verification shown elsewhere on the board was read through the page-'
                      'retrieval tool and is stored with its URL and read time in data/release_checks.json.'
                      ' The shell itself still has no outbound route (FL-077), which is why no '
                      'OLBG HTML capture can be produced from here.'),
        },
        'totals': {
            'sports_listed': len(sports),
            'sports_with_rows': sum(1 for s in sports if s['root_rows'] or s['olbg_rows']),
            'sports_meeting_target': sum(1 for s in sports if s['meets_target']),
            'live_high_root': sum(s['root_high'] for s in sports),
            'live_high_olbg': sum(s['olbg_high'] for s in sports),
            'live_high_union': sum(s['live_high_union'] for s in sports),
            'root_rows': sum(s['root_rows'] for s in sports),
            'olbg_rows': sum(s['olbg_rows'] for s in sports),
            'target_picks_if_all_sports_met': len(sports) * TARGET_PER_SPORT,
            'shortfall_to_target': max(0, len(sports) * TARGET_PER_SPORT - sum(s['live_high_union'] for s in sports)),
        },
        'sports': sports,
        'prose_evidence': evidence,
        'cross_track': {
            'description': (
                'Fixtures captured on both tracks are priced by two independent models. Where they '
                'disagree on the selection, both versions are published and listed here for review. '
                'A disagreement is not evidence that either side is wrong, and neither is a '
                'bookmaker price.'
            ),
            'paired_fixtures': pairs,
            'same_selection': agree,
            'different_selection': len(disagree),
            'withheld_by_one_track': missing,
            'rows': sorted(disagree, key=lambda r: (r['sport'], r['event_id'])),
        },
    }

    return doc


def main():
    doc = build()
    (D / 'brief_coverage.json').write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    t = doc['totals']
    xt = doc['cross_track']
    print(f"sports={t['sports_listed']} with_rows={t['sports_with_rows']} "
          f"meeting_{TARGET_PER_SPORT}_target={t['sports_meeting_target']}")
    print(f"live HIGH root={t['live_high_root']} olbg={t['live_high_olbg']} union={t['live_high_union']} "
          f"shortfall={t['shortfall_to_target']}")
    print(f"cross-track paired={xt['paired_fixtures']} agree={xt['same_selection']} "
          f"differ={xt['different_selection']} withheld={xt['withheld_by_one_track']}")
    ev = doc['prose_evidence']
    print(f"prose root={ev['root']['pieces']} (HIGH {ev['root']['high']}, min {ev['root']['words_min']}w, "
          f"third-party hosts {len(ev['root']['hosts_outside_official_set'])}) "
          f"olbg={ev['olbg']['pieces']} (HIGH {ev['olbg']['high']}, min {ev['olbg']['words_min']}w)")


if __name__ == '__main__':
    main()
