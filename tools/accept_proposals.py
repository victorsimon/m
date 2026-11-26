#!/usr/bin/env python3
"""Remove accepted proposal metadata from the draft and glossary after a PR merge."""
import re
from pathlib import Path

from measure import HEADER


def accept(text):
    lines = []
    for line in text.splitlines(keepends=True):
        header = HEADER.match(line.rstrip("\r\n"))
        if header:
            metadata = header[2]
            cleaned = re.sub(r"(^|;)\s*status:\s*proposal\s*(?=;|$)", "", metadata)
            if cleaned != metadata:
                line = line.replace("{" + metadata + "}", "{" + cleaned.lstrip("; ") + "}", 1)
        elif re.fullmatch(r"# (?:Task-resolution methodology|Glossary) — v\d+ \(status: proposal\)", line.rstrip("\r\n")):
            line = line.replace(" (status: proposal)", "")
        lines.append(line)
    return "".join(lines)


if __name__ == "__main__":
    for path in (Path("docs/glossary.md"), Path("docs/methodology-draft.md")):
        original = path.read_bytes().decode("utf-8")
        accepted = accept(original)
        if accepted != original:
            path.write_bytes(accepted.encode("utf-8"))
