"""Do not turn OLBG links, an inaccessible page or robots denial into fixture facts."""
import datetime as dt
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from discovery import EventLinks, collect

NOW = dt.datetime(2026, 10, 22, 12, tzinfo=dt.timezone.utc)
URL = '/betting-tips/Tennis/All_Tennis/All_Events/A_vs_B/3?event_id=42'


class Discovery(unittest.TestCase):
    def test_actual_text_deduplicated_not_reconstructed_from_slug(self):
        parser = EventLinks(3)
        parser.feed(f'<a href="{URL}"><strong>A &amp; B vs C</strong></a>'
                    f'<a href="{URL}">A to win 2–0</a>')
        self.assertEqual(len(parser.events), 1)
        self.assertEqual(parser.events['42']['title'], 'A & B vs C')

    def test_wrong_sport_external_and_script_links_ignored(self):
        parser = EventLinks(3)
        parser.feed(f'<a href="{URL.replace("/3?", "/1?")}">Football</a>'
                    f'<a href="https://evil.example{URL}">Other</a>'
                    f'<script><a href="{URL}">fake</a></script>')
        self.assertEqual(parser.events, {})

    def test_no_title_means_no_invented_name(self):
        parser = EventLinks(3)
        parser.feed(f'<a href="{URL}"></a>')
        self.assertEqual(parser.events, {})

    def test_robots_denied_prevents_listing_request(self):
        calls = []
        def fetch(url):
            calls.append(url)
            return b'User-agent: *\nDisallow: /\n'
        result = collect(NOW, fetch, sports={'Tennis': 3})
        self.assertEqual(calls, ['https://www.olbg.com/robots.txt'])
        self.assertEqual(result['events'], [])
        self.assertEqual(result['sources'][0]['state'], 'robots_denied')

    def test_failed_robots_is_not_permission(self):
        calls = []
        def fetch(url):
            calls.append(url)
            raise OSError('offline')
        result = collect(NOW, fetch, sports={'Tennis': 3})
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['sources'][0]['state'], 'not_fetched')

    def test_parseable_listing_remains_partial_and_unverified(self):
        def fetch(url):
            return (b'User-agent: *\nAllow: /\n' if url.endswith('robots.txt') else
                    f'<a href="{URL}">A vs B</a><button>Load More Tips</button>'.encode())
        result = collect(NOW, fetch, sports={'Tennis': 3})
        self.assertFalse(result['complete'])
        self.assertEqual(result['sources'][0]['pagination'], 'load-more present')
        row = result['events'][0]
        self.assertEqual(row['verification'], 'unverified')
        for field in ['start_utc', 'competition', 'winner', 'confidence', 'price', 'handicap', 'total']:
            self.assertIsNone(row[field], field)

    def test_challenge_or_empty_html_never_means_zero_verified_matches(self):
        def fetch(url):
            return b'User-agent: *\nAllow: /\n' if url.endswith('robots.txt') else b'<h1>Just a moment</h1>'
        result = collect(NOW, fetch, sports={'Tennis': 3})
        self.assertEqual(result['sources'][0]['state'], 'unverified')
        self.assertIsNone(result['sources'][0]['fetched_at'])

    def test_excluded_sport_cannot_enter_discovery(self):
        with self.assertRaises(ValueError):
            collect(NOW, lambda _: b'', sports={'Football': 1})
