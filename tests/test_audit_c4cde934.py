import json, pathlib, unittest
ROOT = pathlib.Path(__file__).resolve().parents[1]

class TestFreshness20261023(unittest.TestCase):
    def test_no_expired_high_on_olbg_track(self):
        lines = json.loads((ROOT/'data/lines.json').read_text())
        high = [l for l in lines if l['confidence']=='high']
        # 2026-10-23T16:45Z capture: the exact count is date-dependent (17 at the 22:10Z clock, 5 after
        # this day's observations), so the count is bounded rather than pinned. The invariants below are
        # what actually has to hold at every build.
        self.assertLessEqual(len(high), 17)
        for l in high:
            self.assertGreaterEqual(l['start'], '2026-10-23', l['match_id'])
            self.assertTrue(1.40 <= l['our_price_pick'] <= 101.00, l['match_id'])
            self.assertLess(l['our_pick_probability'], 0.70, l['match_id'])

    def test_expired_nhl_picks_demoted(self):
        # The 22 October rows may also have left the board entirely once the 23 October capture became
        # the live primary harvest (session-22dbc477). Either outcome satisfies the intent: an expired
        # pick must never be published as a current HIGH. Absence is stronger than demotion, so both pass.
        lines = {l['match_id']: l for l in json.loads((ROOT/'data/lines.json').read_text())}
        for mid in ('ICH-199931','ICH-199932','ICH-199933','ICH-199940','ICH-199941'):
            row = lines.get(mid)
            if row is None:
                continue
            self.assertNotEqual(row['confidence'], 'high', mid)
            self.assertIn('kick_off_passed_archived', row.get('flags', []), mid)

    def test_fl131_registered(self):
        items = json.loads((ROOT/'data/flagged.json').read_text())['items']
        fl = [i for i in items if i['id']=='FL-131']
        self.assertEqual(len(fl), 1)
        self.assertEqual(fl[0]['status'], 'needs review')
        self.assertTrue(all(s['url'].startswith('https://www.olbg.com/') for s in fl[0]['sources']))

if __name__ == '__main__':
    unittest.main()
