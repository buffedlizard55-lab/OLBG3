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

CAPTURE_DATE = dt.date(2026, 10, 21)   # data/events.json -> "generated"
AS_OF = dt.date(2026, 10, 22)          # this session's build date; fixed for reproducibility
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
        day = capture if m.group(1) == "Today" else capture + dt.timedelta(days=1)
        return day.isoformat(), "derived from capture date"
    m = _DATED.match(label)
    if m:
        day, mon, year, _h, _mi = m.groups()
        month = _MONTHS.get(mon)
        if not month:
            return None, f"unrecognised month {mon!r}"
        if year:
            return dt.date(int(year), month, int(day)).isoformat(), "stated in label"
        y = capture.year
        if month < capture.month:
            y += 1
        return dt.date(y, month, int(day)).isoformat(), "derived from capture year"
    return None, f"unrecognised label {label!r}"


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
