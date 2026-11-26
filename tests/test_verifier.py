import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
import urllib.error  # noqa: E402
from unittest import mock  # noqa: E402

import verifier  # noqa: E402
from verifier import TransportError, decide, thresholds, urlopen_retry, validate  # noqa: E402


def row(label, p, model="m", kind="k"):
    return {"kind": kind, "model": model, "label": label, "p": p}


class ThresholdTest(unittest.TestCase):
    def test_separable(self):
        t = thresholds([row(True, 0.9), row(True, 0.8), row(False, 0.1), row(False, 0.3)])["k|m"]
        self.assertEqual((t["tau_yes"], t["tau_no"], t["passes"]), (0.8, 0.3, True))

    def test_overlap_is_allowed_and_escalates(self):
        t = thresholds([row(True, 0.4), row(True, 0.9), row(False, 0.1), row(False, 0.6)])["k|m"]
        self.assertTrue(t["passes"])
        self.assertEqual((decide([0.7], t), decide([0.3], t), decide([0.5], t), decide([0.6], t), decide([0.4], t)),
                         (True, False, None, None, None))

    def test_transport_is_incomplete_not_failure(self):
        t = thresholds([row(True, 0.9), dict(row(False, None), transport=True)])["k|m"]
        self.assertEqual((t["failures"], t["incomplete"], t["passes"]), (0, 1, False))
        th = {"k|m": {"tau_yes": 0.8, "tau_no": 0.3}}
        v = validate([dict(row(True, 0.9), id="a"), dict(row(True, 0.95), id="a"), dict(row(True, None), id="a", transport=True)], th)["k|m"]
        self.assertEqual((v["wrong"], v["escalated"], v["failures"], v["incomplete"], v["passes"]), (0, 0, 0, 1, False))

    def test_failure_fails(self):
        self.assertFalse(thresholds([row(True, 0.9), row(False, 0.1), row(True, None)])["k|m"]["passes"])


    def test_decide_and_validate(self):
        t = {"tau_yes": 0.8, "tau_no": 0.3}
        self.assertEqual((decide([0.9, 0.95], t), decide([0.1, 0.2], t), decide([0.9, 0.5], t)), (True, False, None))
        th = {"k|m": t}
        rows = [dict(row(True, 0.9), id="a"), dict(row(True, 0.1), id="b"), dict(row(False, 0.5), id="c"), dict(row(False, 0.31), id="d")]
        v = validate(rows, th)["k|m"]
        self.assertEqual((v["wrong"], v["wrong_ids"], v["escalated"], v["passes"]), (1, ["b"], 2, False))


class RedundancyTest(unittest.TestCase):
    def test_mutually_redundant_elements_count_twice(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            glossary, doc, th, record = (root / name for name in ("glossary.md", "doc.md", "thresholds.json", "record.jsonl"))
            glossary.write_text("[GLO.1] {kind: definition; defines: Task; variants: task}\nA unit of work.\n")
            text = "Every [[task]] has an owner.\n"
            doc.write_text("[TSK.1] {kind: rule; derives: INTENT}\n" + text
                           + "[TSK.2] {kind: rule; derives: INTENT}\n" + text)
            tasks = verifier.redundancy_tasks(glossary, doc)
            self.assertEqual([t[1] for t in tasks], [("TSK.1",), ("TSK.2",)])
            plain = "Every task has an owner."
            self.assertEqual([t[2] for t in tasks], [{"target": plain, "context": [plain]}] * 2)
            # Recorded unanimous yes votes exercise the real CLI without model calls.
            ps = {model: [1.0] * runs for model, runs in verifier.PANELS["redundancy"].items()}
            th.write_text(json.dumps({f"redundancy|{model}": {"tau_yes": 0.8, "tau_no": 0.2} for model in ps}))
            record.write_text(json.dumps({"kind": "redundancy", "input_hash": verifier.input_hash(tasks[0][2]),
                                          "template": verifier.TEMPLATE_HASH, "ps": ps}) + "\n")
            result = subprocess.run([sys.executable, str(Path(verifier.__file__)), "judge",
                                     str(glossary), str(doc), str(th), str(record)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("judged=2\tdefect=2\teconomy=2\tclean=0\tescalated=0\tincomplete=0", result.stdout)
            decisions = [json.loads(line) for line in record.read_text().splitlines()]
            self.assertEqual([r["ids"] for r in decisions], [["TSK.1"], ["TSK.2"]])
            self.assertTrue(all(r["decision"] is True for r in decisions))


def http(code, retry_after=None):
    return urllib.error.HTTPError("u", code, "x", {"Retry-After": retry_after} if retry_after else {}, None)


class RetryTest(unittest.TestCase):
    def run_with(self, effects, now=1000.0):
        waits = []
        with mock.patch.object(verifier.urllib.request, "urlopen", side_effect=effects) as op:
            try:
                result = urlopen_retry("req", 1, sleep=waits.append, now=lambda: now)
            except Exception as exc:
                result = exc
        return result, waits, op.call_count

    def test_retries_then_succeeds(self):
        self.assertEqual(self.run_with([http(429), http(503), http(429), "ok"]), ("ok", [1, 2, 4], 4))

    def test_retry_after_seconds_date_small_invalid(self):
        self.assertEqual(self.run_with([http(503, "10"), "ok"])[1], [10.0])
        self.assertEqual(self.run_with([http(503, "Thu, 01 Jan 1970 00:16:50 GMT"), "ok"])[1], [10.0])
        self.assertEqual(self.run_with([http(503, "0"), "ok"])[1], [1])
        self.assertEqual(self.run_with([http(503, "soon"), "ok"])[1], [1])

    def test_exhausted_is_transport_error(self):
        result, waits, calls = self.run_with([http(503)] * 4)
        self.assertIsInstance(result, TransportError)
        self.assertEqual((waits, calls), ([1, 2, 4], 4))

    def test_other_errors_are_not_retried(self):
        for exc in (http(401), http(500), TimeoutError()):
            result, waits, calls = self.run_with([exc])
            self.assertIs(result, exc)
            self.assertEqual((waits, calls), ([], 1))


if __name__ == "__main__":
    unittest.main()
