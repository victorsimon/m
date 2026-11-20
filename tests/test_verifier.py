import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from verifier import thresholds  # noqa: E402


def row(label, p, model="m", kind="k"):
    return {"kind": kind, "model": model, "label": label, "p": p}


class ThresholdTest(unittest.TestCase):
    def test_separable(self):
        t = thresholds([row(True, 0.9), row(True, 0.8), row(False, 0.1), row(False, 0.3)])["k|m"]
        self.assertEqual((t["tau_yes"], t["tau_no"], t["passes"]), (0.3, 0.8, True))

    def test_overlap_fails(self):
        self.assertFalse(thresholds([row(True, 0.5), row(False, 0.5)])["k|m"]["passes"])

    def test_failure_fails(self):
        self.assertFalse(thresholds([row(True, 0.9), row(False, 0.1), row(True, None)])["k|m"]["passes"])


if __name__ == "__main__":
    unittest.main()
