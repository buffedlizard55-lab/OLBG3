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
def build_date():
    """Use UTC today; an explicit ISO override reproduces an archived build.

    The capture date must never double as the expiry clock. Invalid overrides
    fail closed instead of silently publishing picks against the wrong date.
    """
    override = os.environ.get("OLBG_AS_OF")
    if override is not None:
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", override):
            raise ValueError("OLBG_AS_OF must be an ISO date (YYYY-MM-DD)")
        return dt.date.fromisoformat(override)
    return dt.datetime.now(dt.timezone.utc).date()


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


# The clock attached to an OLBG label is not the venue's local time and OLBG never names a zone.
# Every row we have been able to compare converts to the organiser's own start time when the label is
# read as US Eastern (UTC-4 in October, i.e. EDT): 13:00 -> 19:00 CEST handball, 04:00 -> 13:00 Almaty,
# 08:00 -> 14:00 Lyon, 09:00 -> 13:30-15:00 Brussels. That reading is used ONLY to publish a derived
# UTC clock and to show whether a same-day kick-off has already passed at build time. It never moves a
# kick-off date and it never changes a confidence grade (grades must stay reproducible from the
# committed data, which the hourly CI rebuild re-derives).
EASTERN_OFFSET_HOURS = 4


def resolve_kickoff_utc(label, capture=CAPTURE_DATE):
    """Return the derived UTC kick-off ('YYYY-MM-DDTHH:MMZ') or (None, reason).

    Derived, never an OLBG value: the label clock is read as US Eastern (see EASTERN_OFFSET_HOURS).
    """
    label = (label or "").strip()
    m = _LABEL.match(label)
    hours = minutes = None
    if m:
        if int(m.group(2)) > 23 or int(m.group(3)) > 59:
            return None, "invalid clock in label"
        day = capture if m.group(1) == "Today" else capture + dt.timedelta(days=1)
        hours, minutes = int(m.group(2)), int(m.group(3))
    else:
        m = _DATED.match(label)
        if not m:
            return None, f"unrecognised label {label!r}"
        day_s, mon, year, hh, mi = m.groups()
        month = _MONTHS.get(mon)
        if not month:
            return None, f"unrecognised month {mon!r}"
        if int(hh) > 23 or int(mi) > 59:
            return None, "invalid clock in label"
        y = int(year) if year else capture.year + (month < capture.month)
        try:
            day = dt.date(y, month, int(day_s))
        except ValueError:
            return None, "invalid calendar date in label"
        hours, minutes = int(hh), int(mi)
    moment = dt.datetime(day.year, day.month, day.day, hours, minutes, tzinfo=dt.timezone.utc)
    moment += dt.timedelta(hours=EASTERN_OFFSET_HOURS)
    return moment.strftime("%Y-%m-%dT%H:%MZ"), "OLBG clock read as US Eastern (UTC-4)"


def started(label, now_utc=None, capture=CAPTURE_DATE):
    """True when the derived kick-off is at or before `now_utc` (default: the real UTC clock)."""
    iso, _reason = resolve_kickoff_utc(label, capture)
    if not iso:
        return None
    moment = dt.datetime.strptime(iso, "%Y-%m-%dT%H:%MZ").replace(tzinfo=dt.timezone.utc)
    now_utc = now_utc or dt.datetime.now(dt.timezone.utc)
    return moment <= now_utc


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
