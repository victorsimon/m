import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from measure import measure  # noqa: E402

GLOSSARY = """# Glossary

[GLO.1] {kind: definition; defines: Task; variants: task, tasks}
A piece of work.

[GLO.2] {kind: definition; defines: Party; variants: party}
Someone who carries out a [[task]] and uses a [[level]].

[GLO.3] {kind: definition; defines: Level; variants: level}
A step of a [[level]].

[GLO.4] {kind: definition; defines: Task; variants: job}
Duplicate definition.
"""

DOC = """# Doc

stray line
[GOOD.1] {kind: rule; derives: INTENT}
A [[task]] is done by a [[party]] (`task`).

[BAD.1] {kind: rule; derives: NOWHERE}
A task with an [[escalation board]], usually and sometimes.

[BAD.2] {kind: claim; derives: GOOD.1}
Verified in 40 teams.

[BAD.3] {kind: rule; derives: GOOD.1}
La tarea es para el grupo y que se hace.

[BAD.4] {kind: opinion}
Nothing.
"""


class MeasureTest(unittest.TestCase):
    def test_counts(self):
        with tempfile.TemporaryDirectory() as d:
            g, doc = Path(d, "glossary.md"), Path(d, "doc.md")
            g.write_text(GLOSSARY)
            doc.write_text(DOC)
            V = measure([g, doc])
        by = Counter(v[0] for v in V)
        details = {(v[0], v[1], v[2]) for v in V}
        self.assertIn(("form", "doc.md:3", "stray text"), details)
        self.assertIn(("form", "BAD.1", "unmarked 'task'"), details)
        self.assertIn(("form", "GLO.3", "definition uses its own term"), details)
        self.assertIn(("form", "BAD.4", "invalid kind 'opinion'"), details)
        self.assertIn(("form", "BAD.4", "missing key 'derives'"), details)
        self.assertTrue(any(v[0] == "form" and v[1] == "BAD.3" and "Spanish" in v[2] for v in V))
        self.assertIn(("completeness", "BAD.1", "'escalation board' not defined"), details)
        self.assertIn(("order", "GLO.2", "'Level' used before GLO.3"), details)
        self.assertIn(("sharpness", "GLO.4", "'Task' has 2 definitions"), details)
        self.assertIn(("sharpness", "BAD.1", "vague 'usually'"), details)
        self.assertIn(("sharpness", "BAD.1", "vague 'sometimes'"), details)
        self.assertIn(("truthfulness", "BAD.2", "claim without evidence"), details)
        self.assertIn(("fit", "BAD.1", "not traceable to INTENT or AGREEMENT"), details)
        self.assertIn(("fit", "BAD.4", "not traceable to INTENT or AGREEMENT"), details)
        self.assertNotIn("GOOD.1", {v[1] for v in V})
        self.assertEqual(by["truthfulness"], 1)
        self.assertEqual(by["completeness"], 1)

    def test_structure_rules(self):
        doc = """[GLO.1] {kind: definition; defines: Task; variants: task, job}
A piece of work.

[GLO.2] {kind: definition; defines: Chore; variants: job}
A small piece of work.

[A.1] {kind: claim; derives: INTENT; evidence: a source}
A [[task]] and a [[chore]] exist; `task` is literal.

[A.1] {kind: rule; derives: A.1}
A [[job]].

[A.2] {kind: rule derives: INTENT}
Text.

[A.3]{kind: rule; derives: INTENT}
"""
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, "doc.md")
            p.write_text(doc)
            details = {(v[0], v[1], v[2]) for v in measure([p])}
        self.assertIn(("form", "A.1", "duplicate identifier"), details)
        self.assertIn(("form", "A.2", "invalid kind 'rule derives: INTENT'"), details)
        self.assertIn(("form", "A.2", "missing key 'derives'"), details)
        self.assertIn(("form", "doc.md:16", "malformed header"), details)
        self.assertIn(("sharpness", "job", "variant declared by ['Chore', 'Task']"), details)
        self.assertNotIn("truthfulness", {v[0] for v in details})
        self.assertFalse(any(v[2] == "unmarked 'task'" for v in details))


if __name__ == "__main__":
    unittest.main()
