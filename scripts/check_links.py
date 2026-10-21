#!/usr/bin/env python3
"""Fail if any local (relative) link or asset in the generated site is broken."""
import glob, os, re, sys
from urllib.parse import unquote, urlparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pages = glob.glob(os.path.join(ROOT, "*.html")) + glob.glob(os.path.join(ROOT, "sports", "*.html"))
ATTR = re.compile(r'(?:href|src)="([^"]+)"')
bad = []
checked = 0
for page in pages:
    base = os.path.dirname(page)
    html_txt = open(page, encoding="utf-8").read()
    for link in ATTR.findall(html_txt):
        u = urlparse(link)
        if u.scheme in ("http", "https", "mailto") or link.startswith("#") or link.startswith("//"):
            continue
        target = os.path.normpath(os.path.join(base, unquote(u.path)))
        checked += 1
        if not os.path.exists(target):
            bad.append((os.path.relpath(page, ROOT), link))
print(f"pages={len(pages)} local_links_checked={checked} broken={len(bad)}")
for b in bad:
    print("  BROKEN", b[0], "->", b[1])
sys.exit(1 if bad else 0)
