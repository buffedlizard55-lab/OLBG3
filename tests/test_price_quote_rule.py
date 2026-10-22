"""Regression tests for the written-piece price rule in scripts/check_board.py.

The rule exists because prose is hand-written while every row is re-priced on each rebuild.
A selection label of the form "Team to win at 1.61 (-164)" used to escape the checker, which
only matched the "+732 / 7.32" style; five snooker pieces had drifted from their rows before
the gap was found on 2026-10-22. These tests pin the fixed behaviour in both directions.
"""
import importlib.util
import os
import sys
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
spec = importlib.util.spec_from_file_location("check_board", os.path.join(ROOT, "scripts", "check_board.py"))
check_board = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_board)


def row(price, us):
    return {"pick": {"price": price, "american": us}}


def pred(selection, body="A sentence long enough to clear the thirty word floor used by the checker. " * 3):
    return {"selection": selection, "body": body, "status": "analysis",
            "sources": [{"url": "https://example.com/source"}]}


class PriceQuoteRule(unittest.TestCase):
    def setUp(self):
        check_board.errors.clear()
        check_board.warnings.clear()

    def test_stale_selection_price_fails(self):
        check_board.check_predictions({"X-1": pred("Team to win at 1.61 (-164)")},
                                      {"X-1"}, {"X-1": row(1.42, -238)})
        self.assertTrue(any("selection prose quotes decimal 1.61" in e for e in check_board.errors),
                        check_board.errors)

    def test_matching_selection_price_passes(self):
        check_board.check_predictions({"X-1": pred("Team to win at 1.42 (-238)")},
                                      {"X-1"}, {"X-1": row(1.42, -238)})
        self.assertEqual(check_board.errors, [])

    def test_handicap_quote_is_not_a_win_price(self):
        selection = ("Team to win the match (money line 1.42 / -238); handicap angle Team -1.5 goals at 1.91")
        check_board.check_predictions({"X-1": pred(selection)}, {"X-1"}, {"X-1": row(1.42, -238)})
        self.assertEqual(check_board.errors, [], check_board.errors)

    def test_stale_us_odds_in_selection_fails(self):
        check_board.check_predictions({"X-1": pred("Team to win at 1.42 (-200)")},
                                      {"X-1"}, {"X-1": row(1.42, -238)})
        self.assertTrue(any("selection prose quotes -200" in e for e in check_board.errors),
                        check_board.errors)


if __name__ == "__main__":
    unittest.main()
