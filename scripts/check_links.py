#!/usr/bin/env python3
"""Check local pages/assets/fragments in both Pages publication trees.

External URLs are deliberately not fetched: passing this check is not evidence
that an official source is available or supports a sporting claim.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.links = []
        self.anchors = set()
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        for name, value in attrs:
            if value is None:
                continue
            if name in ('href', 'src'):
                self.links.append(value)
            if name == 'id' or (tag == 'a' and name == 'name'):
                self.anchors.add(value)

    handle_startendtag = handle_starttag


def published_pages(root):
    """Legacy publisher serves root, sports/ and olbg/; artifact serves site/."""
    pages = set(root.glob('*.html'))
    for directory in ('sports', 'olbg', 'site', 'daily'):
        pages.update((root / directory).rglob('*.html'))
    return sorted(pages)


def check_tree(root):
    root = Path(root).resolve()
    pages = published_pages(root)
    parsed = {}
    errors = []
    checked = 0

    def parse(path):
        if path not in parsed:
            parsed[path] = Page(path.read_text(encoding='utf-8'))
        return parsed[path]

    for page in pages:
        # Each publishing method has its own document root.
        site = root / 'site'
        publication_root = site if page.is_relative_to(site) else root
        for link in parse(page).links:
            try:
                url = urlsplit(link)
            except ValueError:
                errors.append((str(page.relative_to(root)), link, 'malformed URL'))
                continue
            if url.scheme or url.netloc:
                continue  # External links, data URIs, mailto, etc. are not verified here.
            checked += 1
            path = unquote(url.path)
            # Pages uses /OLBG3/ as its base path, not the origin root.
            if path.startswith('/OLBG3/'):
                target = publication_root / path[len('/OLBG3/'):]
            elif path.startswith('/'):
                errors.append((str(page.relative_to(root)), link, 'outside project base /OLBG3/'))
                continue
            else:
                target = page.parent / path if path else page
            target = target.resolve()
            if not target.is_relative_to(publication_root):
                errors.append((str(page.relative_to(root)), link, 'escapes publication root'))
                continue
            if target.is_dir():
                target = target / 'index.html'
            if not target.is_file():
                errors.append((str(page.relative_to(root)), link, 'missing file'))
            elif url.fragment and target.suffix.lower() in ('.html', '.htm'):
                fragment = unquote(url.fragment)
                # Text fragments are browser directives, not element IDs.
                fragment = fragment.split(':~:text=', 1)[0]
                if fragment and fragment not in parse(target).anchors:
                    errors.append((str(page.relative_to(root)), link, 'missing fragment ID'))
    return len(pages), checked, errors


def main():
    pages, checked, errors = check_tree(ROOT)
    print(f'pages={pages} local_links_checked={checked} broken={len(errors)}')
    for page, link, reason in errors:
        print(f'  BROKEN {page} -> {link} ({reason})')
    return bool(errors)


if __name__ == '__main__':
    raise SystemExit(main())
