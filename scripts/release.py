"""Conservative, shared publication gate. Model confidence is NOT a clock or a fact.

Only a dated source observation in release_checks.json can establish an upcoming
UTC start. Bare OLBG clocks, source hostnames, session ordering, and 'followed by'
never establish an exact start. After 24 h without a new source check, or at the
published start, a HIGH research pick becomes labelled analysis. No outcome is
inferred from the clock ("start window reached" does not mean "final").
"""
import datetime as dt
import json
from pathlib import Path
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
import re

ROOT = Path(__file__).resolve().parents[1]
UTC = dt.timezone.utc
MAX_SOURCE_AGE = dt.timedelta(hours=24)
FIXED_ZONES = {'UTC': 0, 'GMT': 0, 'CEST': 2, 'CET': 1, 'EEST': 3,
               'EET': 2, 'CAT': 2, 'SAST': 2, 'TRT': 3, 'PKT': 5,
               'IST': 5.5, 'JST': 9, 'ALMT': 5, 'CST': 8}


# Explicitly reviewed clock-source domains in the committed release evidence.
# This is a structural trust boundary, NOT verification of page contents.
OFFICIAL_CLOCK_HOSTS = frozenset({
    'api-web.nhle.com', 'en.volleyballworld.com', 'gaacork.ie',
    'www.eurohandball.com', 'www.euroleaguebasketball.net',
    'www.formula1.com', 'www.icc-cricket.com', 'www.leinsterrugby.ie',
    'www.mlb.com', 'www.nrl.com', 'www.pdc.tv', 'www.pgatour.com',
    'www.shl.se', 'www.wst.tv',
    # The Swedish Ice Hockey Association publishes the SHL schedule and its clock on its own
    # stats portal (stats.swehockey.se), not on shl.se. Federation domain, reviewed 2026-10-22.
    'stats.swehockey.se',
    # Midday 2026-10-22 governing-body domains reviewed in session-a0a7003c:
    # WTA/ATP official Order of Play PDFs, BCCI official match centre, JGTO, and Ligue Nationale de Volley.
    'wtafiles.wtatennis.com', 'protennislive.com', 'www.bcci.tv', 'www.jgto.org', 'www.lnv.fr',
    # Evening 2026-10-22 governing-body domains reviewed in session-784afe97: the United Rugby
    # Championship's own competition site publishes its Round 4 fixture list with an explicit
    # 'KO <time> IRE & UK' label, which is the only zone statement the URC gives.
    'www.unitedrugby.com',
    # Session a1e5112b additions 2026-10-22: ATP, LNR, Liiga, ProTennisLive www-prefix variants
    'www.atptour.com', 'prod2.lnr.fr', 'top14.lnr.fr', 'www.liiga.fi', 'www.protennislive.com',
    # Evening 2026-10-22: the league's own schedule page is the canonical source for NBA tip-off
    # times, which it states explicitly as 'ET'. Reviewed session-cab97f19; structural only.
    'www.nba.com',
})


def official_clock_url(value):
    """Reject unknown/suffix-spoofed hosts; never fetch or certify a claim here."""
    if not isinstance(value, str) or not value or any(c.isspace() or ord(c) < 32 for c in value):
        return False
    try:
        url = urlsplit(value)
        return (url.scheme == 'https' and url.hostname in OFFICIAL_CLOCK_HOSTS
                and url.username is None and url.password is None
                and url.port in (None, 443))
    except ValueError:
        return False


def parse_utc(value):
    moment = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    if moment.tzinfo is None:
        raise ValueError('An explicit source offset is required')
    return moment.astimezone(UTC)


def normalized_start(record):
    """Normalize an explicitly sourced clock, never guess a zone from a venue."""
    if record.get('kind') != 'exact':
        return None
    zone = record.get('timezone')
    if zone == 'ET':
        tz = ZoneInfo('America/New_York')  # explicit source label; DST is date-dependent
    elif zone == 'Irish time':
        tz = ZoneInfo('Europe/Dublin')  # explicit source label ('all kick offs are in Irish time'); DST-aware
    elif zone in FIXED_ZONES:
        tz = dt.timezone(dt.timedelta(hours=FIXED_ZONES[zone]))
    else:
        return None
    # Do not silently overwrite an embedded offset with the separate zone label.
    if not re.fullmatch(r'\d{2}:\d{2}', record['time']):
        raise ValueError('Source clock must be HH:MM without an embedded offset')
    moment = dt.datetime.fromisoformat(record['date'] + 'T' + record['time'])
    return moment.replace(tzinfo=tz).astimezone(UTC)


def checks():
    return json.loads((ROOT / 'data/release_checks.json').read_text())['events']


def assess(event_id, date_hint=None, now=None, records=None):
    from board_dates import snapshot_utc
    now = now or snapshot_utc()
    if now.tzinfo is None:
        raise ValueError('Publication clock must be timezone-aware')
    now = now.astimezone(UTC)
    record = (records if records is not None else checks()).get(str(event_id), {})
    result = dict(status='unverified_start', eligible=False, as_of=now.isoformat(),
                  start_utc=None, checked_at=record.get('checked_at'),
                  source=record.get('source'), expires_at=None,
                  reason='No recently checked official, timezone-qualified exact start. Retained as analysis.')
    if record.get('hold'):
        result.update(status='source_conflict', reason=record['hold'])
        return result
    # Date-only information may archive a row, but can NEVER certify an upcoming pick.
    date = record.get('date') or date_hint
    try:
        if date and dt.date.fromisoformat(date) < now.date():
            result.update(status='past_date', reason='The recorded fixture date has passed; archive only. Outcome not inferred.')
            return result
    except (TypeError, ValueError):
        result.update(reason='Invalid source date; start left unverified.')
        return result
    try:
        start = normalized_start(record)
        if start is None:
            if record:
                result['reason'] = record.get('note') or result['reason']
            return result
        checked = parse_utc(record['checked_at'])
    except (KeyError, TypeError, ValueError):
        result.update(reason='Incomplete or invalid official clock evidence; start left blank.')
        return result
    # These two fields are mechanical UTC conversion of the quoted official source.
    result['start_utc'] = start.isoformat().replace('+00:00', 'Z')
    result['expires_at'] = min(start, checked + MAX_SOURCE_AGE).isoformat().replace('+00:00', 'Z')
    if not official_clock_url(record.get('source')) or not isinstance(record.get('quote'), str) or not record['quote'].strip():
        result.update(status='unverified_start', start_utc=None, expires_at=None,
                      reason='Allowlisted official HTTPS URL and nonblank supporting quote are required; URL presence alone is not verification.')
    elif checked > now:
        result.update(status='unverified_start', reason='Source check is later than the publication clock; cannot certify it yet.')
    elif start <= now:
        result.update(status='start_window_reached', reason='Official scheduled start has passed. May be in play, delayed or settled; not a pre-match pick.')
    elif now - checked >= MAX_SOURCE_AGE:
        result.update(status='stale_source', reason='Official observation is at least 24 hours old. No new source check; research only.')
    else:
        result.update(status='upcoming', eligible=True,
                      reason='Official scheduled start is ahead of this build; observation is under 24 hours old. Not a live score or a proven betting edge.')
    return result


def apply_board(rows, now=None):
    records = checks()
    for r in rows:
        pk = r['pick']
        release = assess(r.get('olbg_event_id'), pk.get('start_iso'), now, records)
        pk['release'] = release
        pk['kickoff_utc'] = release['start_utc']
        pk['clock_basis'] = 'UTC conversion of cited official clock' if release['start_utc'] else 'Official UTC start unverified; OLBG clock not converted'
        pk['kickoff_started'] = release['status'] == 'start_window_reached'
        if release['status'] == 'source_conflict':
            r['model'].update(prices={}, probs={}, handicap=None, total=None)
            r['model'].setdefault('notes', []).append(release['reason'])
            pk.update(side=None, label=None, prob=None, price=None, american=None,
                      in_band=False, confidence='LOW')
        if pk['confidence'] == 'HIGH' and not release['eligible']:
            pk['confidence'] = 'MEDIUM'
        if pk.get('evidence_grade') == 'HIGH' and not release['eligible']:
            pk['note'] = (pk.get('note', '') + ' ' + release['reason']).strip()
    return rows


def apply_lines(lines, matches, now=None):
    records = checks()
    match_map = {m['id']: m for m in matches}
    for line in lines:
        m = match_map[line['match_id']]
        event_id = line['match_id'].split('-', 1)[1]
        release = assess(event_id, m.get('date_iso'), now, records)
        line['release'] = release
        if release['status'] == 'source_conflict':
            for field in ('our_match_probability', 'our_home_probability', 'our_pick',
                          'our_pick_probability', 'our_fair_odds', 'our_price_pick',
                          'our_us_odds_pick', 'our_price_other', 'our_handicap_line',
                          'our_handicap_side', 'our_handicap_unit', 'our_total_line',
                          'our_total_side', 'our_total_unit'):
                line[field] = None
            line['confidence'] = 'low'
            line['our_total_basis'] = 'Withheld: conflicting official scoring inputs'
            line['flags'].append('official_source_conflict_unpriced')
        if line['confidence'] == 'high' and not release['eligible']:
            line['confidence'] = 'medium'
            line['flags'].append('release_' + release['status'])
    return lines


def sync_predictions(path, by_id, id_key, confidence):
    """Statuses are generated metadata; never rewrite the independently authored prose."""
    doc = json.loads(path.read_text())
    for prediction in doc['predictions']:
        row = by_id.get(prediction[id_key])
        if row is None:
            continue
        high = confidence(row) == 'high'
        prediction['status'] = 'high' if high else 'analysis'
        if not high:
            release = row.get('release') or (row.get('pick') or {}).get('release') or {}
            # Only publish the release text when the release gate is what blocked the piece. An
            # 'upcoming' (eligible) row that is not HIGH was stopped by the model/band gate, and
            # quoting the "start is ahead of this build" sentence as the downgrade reason reads as a
            # contradiction on the page. FL-128.
            if release.get('eligible'):
                prediction['downgrade_reason'] = ('Model grade or price-band gate not satisfied; the official '
                                                  'start gate itself is not the blocker for this row.')
            else:
                prediction['downgrade_reason'] = release.get('reason') or 'Model grade or price-band gate not satisfied.'
        else:
            prediction.pop('downgrade_reason', None)
    high_count = sum(p.get('status') == 'high' for p in doc['predictions'])
    doc['note'] = (f'{high_count} pieces currently pass this track’s model, price-band and official-start release gates. '
                   'Other pieces are labelled analysis. Counts change with the publication clock; this is not live-score verification '
                   'or a calibrated win-rate claim. Bookmaker odds were not verified.')
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + '\n')
