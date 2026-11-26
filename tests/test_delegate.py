import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from delegate import aggregate  # noqa: E402


class AggregateTest(unittest.TestCase):
    def test_unanimity_decides(self):
        self.assertEqual(aggregate(["not_redundant"] * 3), "not_redundant")
        self.assertEqual(aggregate(["redundant"] * 3), "redundant")
        self.assertEqual(aggregate(["refer"] * 3), "refer")

    def test_disagreement_refers_and_short_is_incomplete(self):
        self.assertEqual(aggregate(["not_redundant", "not_redundant", "redundant"]), "refer")
        self.assertEqual(aggregate(["not_redundant"] * 2), "incomplete")


if __name__ == "__main__":
    unittest.main()
