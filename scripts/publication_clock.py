#!/usr/bin/env python3
"""Advance only the build/release evaluation clock, never a source observation.

Run once at the start of a publication cycle, then use the normal pipeline.
The committed JSON makes every process in that cycle use the same UTC instant.
"""
import datetime as dt
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def advance(now=None, path=None):
    now = now or dt.datetime.now(dt.timezone.utc)
    if now.tzinfo is None:
        raise ValueError('Publication time requires an explicit timezone')
    now = now.astimezone(dt.timezone.utc).replace(second=0, microsecond=0)
    doc = {
        'publication_as_of': now.isoformat().replace('+00:00', 'Z'),
        'purpose': 'Build/release evaluation only. Does not renew any listing capture or official source check.'
    }
    (path or ROOT / 'data/publication.json').write_text(json.dumps(doc, indent=2) + '\n')
    return doc


if __name__ == '__main__':
    print(json.dumps(advance()))
