import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from accept_proposals import accept  # noqa: E402


class AcceptProposalsTest(unittest.TestCase):
    def test_removes_only_proposal_metadata_and_heading_label(self):
        source = ("# Task-resolution methodology — v5 (status: proposal)\n\n"
                  "[SLP.9] {kind: rule; derives: SLP.3; status: proposal}\n"
                  "The literal `status: proposal` documents the convention.\n"
                  "[SLP.13] {kind: rule; status: proposal; derives: SLP.12}\n"
                  "Body with (status: proposal) is not a heading.\n"
                  "[GLO.1] {status: proposal; kind: definition; defines: Task; variants: task}\n"
                  "A unit of work.\n")
        expected = ("# Task-resolution methodology — v5\n\n"
                    "[SLP.9] {kind: rule; derives: SLP.3}\n"
                    "The literal `status: proposal` documents the convention.\n"
                    "[SLP.13] {kind: rule; derives: SLP.12}\n"
                    "Body with (status: proposal) is not a heading.\n"
                    "[GLO.1] {kind: definition; defines: Task; variants: task}\n"
                    "A unit of work.\n")
        self.assertEqual(accept(source), expected)
        self.assertEqual(accept(expected), expected)

    def test_preserves_other_statuses_and_unmarked_headers(self):
        source = ("[SLP.9] {kind: rule; derives: SLP.3; status: proposal-review}\n"
                  "[SLP.13] { kind: rule; derives: SLP.12 }\n"
                  "[SLP.14] {kind: rule; derives: SLP.12; status: accepted}")
        self.assertEqual(accept(source), source)

    def test_preserves_section_and_unrelated_heading_labels(self):
        source = ("## Section (status: proposal)\n"
                  "# Example heading (status: proposal)\n"
                  "`# Task-resolution methodology — v5 (status: proposal)`\n")
        self.assertEqual(accept(source), source)

    def test_cli_only_changes_draft_and_glossary_and_is_idempotent(self):
        script = Path(__file__).resolve().parent.parent / "tools" / "accept_proposals.py"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            source = b"[SLP.9] {kind: rule; derives: INTENT; status: proposal}\r\nBody.\r\n"
            paths = [root / "docs" / name for name in ("glossary.md", "methodology-draft.md")]
            for path in paths + [root / "CHANGELOG.md"]:
                path.write_bytes(source)
            for _ in range(2):
                subprocess.run([sys.executable, str(script)], cwd=root, check=True)
                for path in paths:
                    self.assertEqual(path.read_bytes(), source.replace(b"; status: proposal", b""))
                self.assertEqual((root / "CHANGELOG.md").read_bytes(), source)

    def test_whitespace_and_crlf(self):
        source = "[SLP.9] {kind: rule; derives: SLP.3; status:  proposal }\r\n"
        self.assertEqual(accept(source), "[SLP.9] {kind: rule; derives: SLP.3}\r\n")


if __name__ == "__main__":
    unittest.main()
