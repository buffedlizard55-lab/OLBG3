"""Display-boundary regressions: no network, invented sporting facts or moving-clock pins."""
import copy
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pick_surface as surface


class PickBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.text = ' '.join(['An individual match analysis with a clear selection and relevant statistics.'] * 4)
        self.sources = [{'label': 'Official league fixture', 'url': 'https://api-web.nhle.com/v1/schedule/2026-10-24'}]
        self.release = {'eligible': True, 'status': 'upcoming', 'source': self.sources[0]['url'],
                        'start_utc': '2026-10-24T23:00:00Z', 'checked_at': '2026-10-24T22:00:00Z'}

    def check(self, price=1.8, text=None, sources=None, release=None):
        return surface.pick_problem('HIGH', self.release if release is None else release, price,
                                    self.text if text is None else text,
                                    self.sources if sources is None else sources)

    def test_valid_boundary(self):
        self.assertEqual(self.check(), '')
        for p in (1.4, 101):
            self.assertEqual(self.check(price=p), '')

    def test_rejects_non_finite_boolean_and_out_of_band_prices(self):
        for p in (None, True, False, '1.8', float('nan'), float('inf'), 1.3999, 101.0001):
            with self.subTest(price=p):
                self.assertTrue(self.check(price=p))

    def test_prose_rules_are_gates_not_just_notices(self):
        for body in ('', 'too short', self.text + ' model', self.text + ' verified'):
            self.assertTrue(self.check(text=body))

    def test_requires_official_clock_and_prose_sources(self):
        self.assertTrue(self.check(sources=[]))
        self.assertTrue(self.check(sources=[{'url': 'https://www.olbg.com/betting-tips'}]))
        release = dict(self.release, source='https://api-web.nhle.com.attacker.example/schedule')
        self.assertTrue(self.check(release=release))
        self.assertTrue(self.check(release=dict(self.release, eligible=False)))

    def test_match_winner_never_inherits_featured_totals_or_handicap(self):
        self.assertEqual(surface.selection_market('fixture'), 'Match winner')
        self.assertEqual(surface.selection_market('race'), 'Race winner')
        self.assertEqual(surface.selection_market('outright'), 'Outright winner')
        for market in ('Game Totals', 'Handicap'):
            row = {'ref': 'TEST-1', 'sport': 'Ice Hockey', 'home': 'Home', 'away': 'Away',
                   'olbg_event_id': 123, 'olbg_market': market,
                   'pick': {'confidence': 'HIGH', 'release': self.release, 'price': 1.8}}
            pred = {'TEST-1': {'body': self.text, 'sources': self.sources}}
            result = surface.collect([row], pred, {}, {}, {})[0]
            self.assertEqual(result['tracks']['root']['market'], 'Match winner')
            self.assertEqual(result['tracks']['root']['captured_market'], market)

    def test_table_links_to_exact_analysis_and_official_source(self):
        t = {'state': 'pick', 'selection': 'Home <unsafe>', 'market': 'Match winner',
             'price': 1.8, 'clock_source': self.sources[0]['url']}
        row = {'state': 'pick', 'key': 'E123', 'sport': 'Ice Hockey', 'match': 'Home v Away',
               'start_utc': self.release['start_utc'], 'tracks': {'root': t}}
        markup = surface.summary_table([row])
        self.assertIn('today.html#pick-E123', markup)
        self.assertIn(self.sources[0]['url'], markup)
        self.assertIn('Home &lt;unsafe&gt;', markup)
        self.assertNotIn('Home <unsafe>', markup)
        self.assertIn('HIGH', markup)
        row['tracks']['olbg'] = dict(t, selection='Away')
        self.assertIn('Selections disagree', surface.summary_table([row]))
        row['state'] = 'analysis'
        self.assertNotIn('pick-E123', surface.summary_table([row]))

    def test_absent_written_piece_cannot_count(self):
        self.assertIn('no written prediction', self.check(text=''))

    def test_collect_does_not_mutate_capture(self):
        lines = {'TEST-123': {'confidence': 'HIGH', 'sport': 'Ice Hockey', 'home': 'Home',
                             'our_pick': 'Home', 'our_price_pick': 1.8, 'release': self.release,
                             'inputs': {'olbg_market': 'Game Totals'}}}
        pred = {'TEST-123': {'text': self.text, 'sources': self.sources}}
        before = copy.deepcopy(lines)
        result = surface.collect([], {}, lines, {}, pred)[0]
        self.assertEqual(lines, before)
        self.assertEqual(result['tracks']['olbg']['market'], 'Match winner')
        self.assertEqual(result['tracks']['olbg']['captured_market'], 'Game Totals')


if __name__ == '__main__':
    unittest.main()

class LatestListingTests(unittest.TestCase):
    def test_entry_missing_from_latest_listing_is_held_without_cancellation_claim(self):
        release = {'eligible': True, 'source': 'https://api-web.nhle.com/v1/schedule/2026-10-24'}
        row = {'ref': 'TEST-1', 'sport': 'Ice Hockey', 'home': 'Home', 'away': 'Away',
               'olbg_event_id': 123, 'pick': {'confidence': 'HIGH', 'price': 1.8, 'release': release}}
        pred = {'TEST-1': {'body': 'A clear selection with statistics and context. ' * 8,
                           'sources': [{'url': release['source']}]}}
        kept = surface.collect([row], pred, {}, {}, {}, active_event_ids={'123'})[0]
        held = surface.collect([row], pred, {}, {}, {}, active_event_ids=set())[0]
        self.assertEqual(kept['state'], 'pick')
        self.assertEqual(held['state'], 'analysis')
        self.assertIn('availability unconfirmed', held['reason'])
        self.assertNotIn('cancelled', held['reason'])

    def test_cutoff_reaches_card_and_shortlist(self):
        t = {'state': 'pick', 'selection': 'Home', 'market': 'Match winner', 'price': 1.8,
             'american': '-125', 'confidence': 'HIGH', 'prob': 0.55, 'text': 'Analysis ' * 40,
             'ref': 'TEST-1', 'clock_source': 'https://api-web.nhle.com/v1/schedule/2026-10-24',
             'expires_at': '2026-10-24T23:00:00Z'}
        x = {'state': 'pick', 'key': 'E123', 'sport': 'Ice Hockey', 'match': 'Home v Away',
             'start_utc': '2026-10-24T23:00:00Z', 'tracks': {'root': t}, 'sources': [], 'competition': ''}
        for markup in (surface.card_html(x), surface.summary_table([x])):
            self.assertIn("data-expires-at='2026-10-24T23:00:00Z'", markup)
        script = (ROOT / 'assets/release.js').read_text()
        self.assertIn("node.setAttribute('data-state', 'analysis')", script)
        self.assertIn("badge.textContent = 'NOT A PICK'", script)

class OfficialProseDomainTests(unittest.TestCase):
    def test_prose_domain_is_not_mistaken_for_clock_domain(self):
        self.assertTrue(surface.official_prose_url('https://www.legavolley.it/classifica/?IdCampionato=999'))
        for url in ('https://www.legavolley.it.attacker.example/', 'https://user@www.legavolley.it/', 'http://www.legavolley.it/'):
            self.assertFalse(surface.official_prose_url(url))
