#!/usr/bin/env python3
"""board_dates.py - resolve OLBG's relative clock labels and convert decimal prices to US odds.

OLBG prints bare labels ("Today 19:10", "Tomorrow 03:00", "23 Oct 12:00", "27 May 2027 06:00")
and never states a time zone. We do NOT convert the clock or invent a zone. We only attach a
calendar date, and only where the label is unambiguous:

  * "Today"    -> the capture date (the date the listing was read)
  * "Tomorrow" -> capture date + 1 day
  * "23 Oct"   -> 23 Oct in the capture year, unless that month has already passed, in which
                  case the next year (OLBG lists future fixtures only)
  * "27 May 2027" -> the stated date, verbatim

The resolved date is a *derived* field. It is used only to decide whether a kick-off has passed
and is labelled as derived on the site. It is never presented as an OLBG value.

Price band: the brief asks for high-confidence picks priced between -250 and +10000 in US
(American) odds. Those convert to decimal 1.40 and 101.00 respectively. `american()` is the
inverse of the standard conversion so the band can be checked arithmetically.
"""
import datetime as dt
import re
import os

CAPTURE_DATE = dt.date(2026, 10, 21)   # data/events.json -> "generated"



def source_snapshot_utc():
    """Newest recorded official observation; publishing must never renew this clock."""
    import json
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data/release_checks.json"), encoding="utf-8") as source:
        doc = json.load(source)
    stamps = [c.get("checked_at") for c in doc.get("events", {}).values() if c.get("checked_at")]
    stamps.append(doc.get("checked_at"))
    newest = max(s for s in stamps if s)
    moment = dt.datetime.fromisoformat(newest.replace("Z", "+00:00"))
    if moment.tzinfo is None:
        raise ValueError("Source observation must have an explicit offset")
    return moment.astimezone(dt.timezone.utc)


def snapshot_utc():
    """Reproducible publication clock, independent of source observation times.

    CI advances data/publication.json once before building. Every subsequent process
    reads the same instant, including builds that cross a minute or UTC midnight.
    OLBG_NOW_UTC reproduces historical builds/tests. No source check is renewed.
    A missing or malformed publication clock fails closed rather than reviving HIGH
    picks at an old source clock.
    """
    import json
    override = os.environ.get("OLBG_NOW_UTC")
    if override is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", override):
            raise ValueError("OLBG_NOW_UTC must be YYYY-MM-DDTHH:MMZ")
        return dt.datetime.strptime(override, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "data/publication.json"), encoding="utf-8") as source:
        stamp = json.load(source)["publication_as_of"]
    if not isinstance(stamp, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:00Z", stamp):
        raise ValueError("Publication clock must be YYYY-MM-DDTHH:MM:00Z")
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def build_date():
    """The stored publication clock's date; OLBG_AS_OF can reproduce an archive.

    CI advances publication.json before a rebuild, independently of the observation
    clocks in release_checks.json. This keeps expiry current and builds reproducible.
    """
    override = os.environ.get("OLBG_AS_OF")
    if override is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", override):
            raise ValueError("OLBG_AS_OF must be an ISO date (YYYY-MM-DD)")
        return dt.date.fromisoformat(override)
    return snapshot_utc().date()


def snapshot_age_hours(now=None):
    """Age of the newest source observation at publication, in hours (never negative).

    Publishing does not reset source age. Use ``now`` or ``OLBG_NOW_UTC`` for
    an explicit later evaluation; the default stays reproducible within a build.
    """
    now = now or snapshot_utc()
    override = os.environ.get("OLBG_NOW_UTC")
    if override:
        now = dt.datetime.strptime(override, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)
    delta = now - source_snapshot_utc()
    return round(max(delta.total_seconds(), 0) / 3600.0, 1)


AS_OF = build_date()
BAND_LOW_DEC = 1.40                    # -250 American: 1 + 100/250
BAND_HIGH_DEC = 101.0                  # +10000 American: 1 + 10000/100
BAND_LOW_US = -250
BAND_HIGH_US = 10000

_MONTHS = {m: i for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"], start=1)}
_LABEL = re.compile(r"^(Today|Tomorrow)\s+(\d{1,2}):(\d{2})$")
_DATED = re.compile(r"^(\d{1,2})\s+([A-Z][a-z]{2})(?:\s+(\d{4}))?\s+(\d{1,2}):(\d{2})$")


def resolve_start(label, capture=CAPTURE_DATE):
    """Return (iso_date_string, source) or (None, reason). Never guesses a clock or a zone."""
    label = (label or "").strip()
    m = _LABEL.match(label)
    if m:
        if int(m.group(2)) > 23 or int(m.group(3)) > 59:
            return None, "invalid clock in label"
        day = capture if m.group(1) == "Today" else capture + dt.timedelta(days=1)
        return day.isoformat(), "derived from capture date"
    m = _DATED.match(label)
    if m:
        day, mon, year, _h, _mi = m.groups()
        month = _MONTHS.get(mon)
        if not month:
            return None, f"unrecognised month {mon!r}"
        if int(_h) > 23 or int(_mi) > 59:
            return None, "invalid clock in label"
        y = int(year) if year else capture.year + (month < capture.month)
        try:
            resolved = dt.date(y, month, int(day))
        except ValueError:
            return None, "invalid calendar date in label"
        return resolved.isoformat(), "stated in label" if year else "derived from capture year"
    return None, f"unrecognised label {label!r}"


# OLBG does not identify the timezone of its bare labels. Matching a few fixtures
# is not permission to assign every sport a US Eastern offset (and UTC-4 is wrong
# in winter). Only scripts/release.py normalizes explicitly sourced official clocks.
def resolve_kickoff_utc(label, capture=CAPTURE_DATE):
    """Unknown timezone -> blank. Kept as an API for archived consumers."""
    date, reason = resolve_start(label, capture)
    return None, ("OLBG timezone unverified; no UTC conversion" if date else reason)


def started(label, now_utc=None, capture=CAPTURE_DATE):
    """A zone-less listing cannot establish whether a fixture has started."""
    return None


def american(decimal_price):
    """Decimal -> US odds, rounded the way a sportsbook quotes them."""
    if not decimal_price or decimal_price <= 1:
        return None
    if decimal_price < 2:
        return int(round(-100.0 / (decimal_price - 1.0)))
    return int(round(100.0 * (decimal_price - 1.0)))


def in_band(decimal_price):
    return bool(decimal_price) and BAND_LOW_DEC <= decimal_price <= BAND_HIGH_DEC


def expired(start_iso, as_of=AS_OF):
    if not start_iso:
        return False
    return dt.date.fromisoformat(start_iso) < as_of
