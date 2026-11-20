import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from verifier import decide, thresholds, validate  # noqa: E402


def row(label, p, model="m", kind="k"):
    return {"kind": kind, "model": model, "label": label, "p": p}


class ThresholdTest(unittest.TestCase):
    def test_separable(self):
        t = thresholds([row(True, 0.9), row(True, 0.8), row(False, 0.1), row(False, 0.3)])["k|m"]
        self.assertEqual((t["tau_yes"], t["tau_no"], t["passes"]), (0.8, 0.3, True))

    def test_overlap_fails(self):
        self.assertFalse(thresholds([row(True, 0.5), row(False, 0.5)])["k|m"]["passes"])

    def test_failure_fails(self):
        self.assertFalse(thresholds([row(True, 0.9), row(False, 0.1), row(True, None)])["k|m"]["passes"])


    def test_decide_and_validate(self):
        t = {"tau_yes": 0.8, "tau_no": 0.3}
        self.assertEqual((decide([0.9, 0.95], t), decide([0.1, 0.2], t), decide([0.9, 0.5], t)), (True, False, None))
        th = {"k|m": t}
        rows = [dict(row(True, 0.9), id="a"), dict(row(True, 0.1), id="b"), dict(row(False, 0.5), id="c"), dict(row(False, 0.31), id="d")]
        v = validate(rows, th)["k|m"]
        self.assertEqual((v["wrong"], v["wrong_ids"], v["escalated"], v["passes"]), (1, ["b"], 2, False))


if __name__ == "__main__":
    unittest.main()
