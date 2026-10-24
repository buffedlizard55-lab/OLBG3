"""Both sides, not two shared words, must identify an official scheduled fixture."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_live as verifier


class FixtureIdentityTests(unittest.TestCase):
    def setUp(self):
        payload = {'gameWeek': [{'games': [{'id': 42, 'startTimeUTC': '2026-10-24T23:00:00Z',
                   'homeTeam': {'abbrev': 'TOR', 'commonName': {'default': 'Maple Leafs'}},
                   'awayTeam': {'abbrev': 'NYR', 'commonName': {'default': 'Rangers'}}}]}]}
        self.game = verifier.nhl_games(payload)[0]

    def test_two_tokens_from_one_team_do_not_establish_opponent(self):
        self.assertFalse(verifier.fixture_identity('Unrelated Team @ TOR Maple Leafs', self.game))
        self.assertFalse(verifier.fixture_identity('NYR Rangers @ Unrelated Team', self.game))

    def test_away_home_orientation_is_required_for_at(self):
        self.assertTrue(verifier.fixture_identity('NY Rangers @ TOR Maple Leafs', self.game))
        self.assertFalse(verifier.fixture_identity('TOR Maple Leafs @ NY Rangers', self.game))

    def test_vs_can_use_either_order_without_inventing_home(self):
        self.assertTrue(verifier.fixture_identity('Rangers vs Maple Leafs', self.game))
        self.assertTrue(verifier.fixture_identity('Maple Leafs v Rangers', self.game))

    def test_ambiguous_or_missing_team_identifiers_are_rejected(self):
        for event in ('Rangers Maple Leafs', 'Rangers @', '@ Maple Leafs', 'Rangers @ Maple Leafs @ Other'):
            self.assertFalse(verifier.fixture_identity(event, self.game))
        self.assertFalse(verifier.fixture_identity('Rangers @ Maple Leafs', {'home_aliases': [], 'away_aliases': []}))

    def test_full_multiword_alias_required(self):
        self.assertFalse(verifier.fixture_identity('Rangers @ Leafs', self.game))
        self.assertFalse(verifier.fixture_identity('Rangers @ Maple', self.game))

    def test_official_mlb_teamname_supports_listing_abbreviations(self):
        payload = {'dates': [{'games': [{'gamePk': 7, 'gameDate': '2026-10-25T00:00:00Z',
                   'teams': {'home': {'team': {'name': 'Milwaukee Brewers', 'teamName': 'Brewers'}},
                             'away': {'team': {'name': 'Tampa Bay Rays', 'teamName': 'Rays'}}}}]}]}
        game = verifier.mlb_games(payload)[0]
        self.assertTrue(verifier.fixture_identity('TB Rays @ MIL Brewers', game))
        self.assertFalse(verifier.fixture_identity('TB Rays @ CHC Cubs', game))

    def test_receipt_identifies_actual_probe_not_previous_session(self):
        note = verifier.probe_note(Path('data/raw/official-fresh'), '2026-10-24T22:30:00Z')
        self.assertIn('official-fresh', note)
        self.assertIn('22:30:00Z', note)
        self.assertNotIn('session-a30d9bdb', note)
        doc = {'session': 'earlier provenance'}
        verifier._append_session(doc, note)
        verifier._append_session(doc, note)
        self.assertEqual(doc['session'].count(note), 1)
        self.assertTrue(doc['session'].startswith('earlier provenance'))


if __name__ == '__main__':
    unittest.main()

class CapturedPriceTests(unittest.TestCase):
    def test_starting_price_is_not_a_numeric_quote(self):
        import importlib.util
        path = Path(__file__).resolve().parents[1] / 'tools/build_dataset.py'
        spec = importlib.util.spec_from_file_location('dataset_price_test', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        for raw in ('SP', '', None, 'NaN', 'inf', '1.0', '-2'):
            self.assertIsNone(module.parse_decimal(raw))
        self.assertEqual(module.parse_decimal('2.05'), 2.05)

class CityAliasTests(unittest.TestCase):
    def test_city_only_shortname_cannot_identify_a_franchise(self):
        aliases = verifier.team_aliases({'name': 'New York Mets', 'teamName': 'Mets', 'shortName': 'New York'})
        self.assertNotIn({'new', 'york'}, aliases)
        self.assertIn({'mets'}, aliases)
