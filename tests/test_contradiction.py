import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from contradiction import aggregate, commands, formal_problem, pairs, score, z3_verdict  # noqa: E402

SMT = '(set-logic UF) ; (check-sat) in a comment\n(declare-const p Bool)\n(assert (! p :named a1))\n(assert (! (not |x)y|) :named b1))'


def reply(smt2=SMT, clauses=None):
    clauses = clauses or [{"source": "a", "assertions": ["a1"]}, {"source": "b", "assertions": ["b1"]}]
    return {"status": "encoded", "smt2": smt2, "clauses": clauses}


class Z3VerdictTest(unittest.TestCase):
    def test_error_invalidates_even_when_sat_follows(self):
        self.assertEqual(z3_verdict('(error "line 5: unknown sort")\nsat\n')[0], "invalid")

    def test_sat_unsat_unknown(self):
        self.assertEqual(z3_verdict("sat\n(model)")[0], "compatible")
        self.assertEqual(z3_verdict("unsat\n(a1 b1)"), ("contradiction", "(a1 b1)"))
        self.assertEqual(z3_verdict("unknown\n")[0], "invalid")
        self.assertEqual(z3_verdict("")[0], "invalid")


class FormalReplyTest(unittest.TestCase):
    def test_commands_skip_comments_and_quoted_symbols(self):
        self.assertEqual(commands(SMT), ["set-logic", "declare-const", "assert", "assert"])

    def test_valid_and_refer(self):
        self.assertIsNone(formal_problem(reply()))
        self.assertIsNone(formal_problem({"status": "refer", "smt2": "", "clauses": [], "note": "two readings"}))

    def test_rejections(self):
        cases = {
            "solver command": reply(SMT + "\n(check-sat)"),
            "unnamed assertion": reply(SMT + "\n(assert p)"),
            "unlisted name": reply(clauses=[{"source": "a", "assertions": ["a1"]}, {"source": "b", "assertions": []}]),
            "one statement only": reply(clauses=[{"source": "a", "assertions": ["a1", "b1"]}]),
            "unbalanced": reply(SMT + "\n(assert"),
            "bad status": {"status": "sat"},
        }
        for name, r in cases.items():
            self.assertIsNotNone(formal_problem(r), name)


class AggregateTest(unittest.TestCase):
    def test_unanimity_or_refer(self):
        self.assertEqual(aggregate(["compatible"] * 3), "compatible")
        self.assertEqual(aggregate(["contradiction"] * 3), "contradiction")
        self.assertEqual(aggregate(["compatible", "compatible", "refer"]), "refer")
        self.assertEqual(aggregate(["contradiction", "compatible", "compatible"]), "refer")
        self.assertEqual(aggregate(["compatible", "compatible"]), "incomplete")


class PairsTest(unittest.TestCase):
    def test_only_pairs_sharing_a_term(self):
        els = [{"id": "A", "uses": {"t"}}, {"id": "B", "uses": {"t", "u"}}, {"id": "C", "uses": {"v"}}]
        self.assertEqual([(a["id"], b["id"]) for a, b in pairs(els)], [("A", "B")])


class ScoreTest(unittest.TestCase):
    def test_invalid_and_wrong_fail_refer_does_not(self):
        labels = {"x": {"contradiction": True}, "y": {"contradiction": False}}
        rows = [{"id": "x", "method": "m", "verdict": "contradiction"}, {"id": "y", "method": "m", "verdict": "refer"},
                {"id": "x", "method": "n", "verdict": "invalid"}, {"id": "y", "method": "o", "verdict": "contradiction"}]
        s = score(rows, labels)
        self.assertEqual((s["m"]["correct"], s["m"]["refer"], s["m"]["passes"]), (1, 1, True))
        self.assertFalse(s["n"]["passes"])
        self.assertEqual((s["o"]["wrong_ids"], s["o"]["passes"]), (["y"], False))


if __name__ == "__main__":
    unittest.main()
