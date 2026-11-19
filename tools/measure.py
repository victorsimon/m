#!/usr/bin/env python3
"""Mechanical slop measurement, as declared in docs/methodology-draft.md (SLP.4-SLP.10).

Usage: tools/measure.py FILE...   (exit 1 if any violation)
Contradiction and redundancy (fit MUS, economy) need judgement and are not computed here.
"""
import re
import sys
from pathlib import Path

LISTS = Path(__file__).resolve().parent.parent / "docs" / "lists"
HEADER = re.compile(r"^\[([A-Z]+\.\d+)\] \{(.*)\}$")
HEADER_LIKE = re.compile(r"^\[[A-Z]+\.\d+\]")
MARK = re.compile(r"\[\[([^\]]+)\]\]")
LITERAL = re.compile(r"`[^`]*`")
KINDS = {"definition", "rule", "claim", "question"}
ROOTS = {"INTENT", "AGREEMENT"}
FIGURES = ["form", "fit", "economy", "completeness", "order", "sharpness", "truthfulness"]


def word_list(name):
    return [w.strip().lower() for w in (LISTS / name).read_text().splitlines() if w.strip()]


def find(word, text):
    """Case-insensitive matches of word at word boundaries (hyphens count as word characters)."""
    return list(re.finditer(r"(?<![\w-])" + re.escape(word) + r"(?![\w-])", text, re.IGNORECASE))


def blank(text, words):
    """Count matches of words, longest first, without overlaps. Returns (matches, remaining text)."""
    hits = []
    for w in sorted(words, key=len, reverse=True):
        for m in reversed(find(w, text)):
            hits.append((w, m.start()))
            text = text[: m.start()] + " " * len(m.group()) + text[m.end():]
    return hits, text


def parse(path, violations):
    elements, cur = [], None
    for n, line in enumerate(path.read_text().splitlines(), 1):
        m = HEADER.match(line)
        if m:
            meta = {}
            for part in m.group(2).split(";"):
                key, sep, val = part.partition(":")
                if not sep:
                    violations.append(("form", m.group(1), f"malformed metadata '{part.strip()}'"))
                    continue
                meta[key.strip()] = val.strip()
            cur = {"id": m.group(1), "meta": meta, "lines": [], "file": path.name}
            elements.append(cur)
        elif HEADER_LIKE.match(line):
            violations.append(("form", f"{path.name}:{n}", "malformed header"))
        elif line.startswith("#"):
            cur = None
        elif line.strip():
            if cur is None:
                violations.append(("form", f"{path.name}:{n}", "stray text"))
            else:
                cur["lines"].append(line)
    for e in elements:
        e["text"] = "\n".join(e["lines"])
        e["kind"] = e["meta"].get("kind")
    return elements


def measure(paths):
    V = []
    els = [e for p in paths for e in parse(Path(p), V)]
    vague, spanish = word_list("vague-words.txt"), set(word_list("spanish-stopwords.txt"))

    seen = set()
    for e in els:
        if e["id"] in seen:
            V.append(("form", e["id"], "duplicate identifier"))
        seen.add(e["id"])
        if e["kind"] not in KINDS:
            V.append(("form", e["id"], f"invalid kind '{e['kind']}'"))
        required = ["defines", "variants"] if e["kind"] == "definition" else ["derives"]
        for key in required:
            if key not in e["meta"]:
                V.append(("form", e["id"], f"missing key '{key}'"))

    defs, owners = {}, {}
    for e in els:
        if e["kind"] == "definition" and "defines" in e["meta"]:
            term = e["meta"]["defines"]
            defs.setdefault(term, []).append(e)
            for f in e["meta"].get("variants", "").split(","):
                if f.strip():
                    owners.setdefault(f.strip().lower(), set()).add(term)
    for term, ds in defs.items():
        if len(ds) > 1:
            V.append(("sharpness", ds[1]["id"], f"'{term}' has {len(ds)} definitions"))
    for f, ts in owners.items():
        if len(ts) > 1:
            V.append(("sharpness", f, f"variant declared by {sorted(ts)}"))
    term_of = {f: sorted(ts)[0] for f, ts in owners.items()}

    undefined = {}
    for e in els:
        marked = [u.strip().lower() for u in MARK.findall(e["text"])]
        e["uses"] = {term_of[u] for u in marked if u in term_of}
        for u in marked:
            if u not in term_of:
                undefined.setdefault(u, e["id"])
        if e["kind"] == "definition" and e["meta"].get("defines") in e["uses"]:
            V.append(("form", e["id"], "definition uses its own term"))
        hits, _ = blank(LITERAL.sub(lambda m: " " * len(m.group()), MARK.sub(lambda m: " " * len(m.group()), e["text"])), owners)
        for w, _pos in hits:
            V.append(("form", e["id"], f"unmarked '{w}'"))
        tokens = set(re.findall(r"[a-záéíóúñü]+", e["text"].lower()))
        if len(tokens & spanish) >= 3:
            V.append(("form", e["id"], f"Spanish words {sorted(tokens & spanish)}"))
        hits, _ = blank(e["text"], vague)
        for w, _pos in hits:
            V.append(("sharpness", e["id"], f"vague '{w}'"))
        if e["kind"] == "claim" and not e["meta"].get("evidence"):
            V.append(("truthfulness", e["id"], "claim without evidence"))
    for u, where in undefined.items():
        V.append(("completeness", where, f"'{u}' not defined"))

    position = {e["id"]: i for i, e in enumerate(els)}
    for e in els:
        for t in sorted(e["uses"]):
            for d in defs.get(t, []):
                if d["file"] == e["file"] and position[d["id"]] > position[e["id"]]:
                    V.append(("order", e["id"], f"'{t}' used before {d['id']}"))

    by_id = {e["id"]: e for e in els}
    memo = {}

    def reaches_root(i, stack=()):
        if i in ROOTS:
            return True
        if i in memo:
            return memo[i]
        e = by_id.get(i)
        if e is None or i in stack or e["kind"] == "definition":
            return False
        targets = [t.strip() for t in e["meta"].get("derives", "").split(",") if t.strip()]
        memo[i] = any(reaches_root(t, stack + (i,)) for t in targets)
        return memo[i]

    traceable = {e["id"] for e in els if e["kind"] != "definition" and reaches_root(e["id"])}
    terms = set().union(*(by_id[i]["uses"] for i in traceable)) if traceable else set()
    while True:
        new = {d["id"] for t in terms for d in defs.get(t, [])} - traceable
        if not new:
            break
        traceable |= new
        terms |= set().union(*(by_id[i]["uses"] for i in new))
    for e in els:
        if e["id"] not in traceable:
            V.append(("fit", e["id"], "not traceable to INTENT or AGREEMENT"))
    return V


def main(paths):
    V = measure(paths)
    for fig, where, detail in sorted(V, key=lambda v: (FIGURES.index(v[0]), v[1])):
        print(f"{fig}\t{where}\t{detail}")
    totals = {f: sum(1 for v in V if v[0] == f) for f in FIGURES}
    print("totals\t" + "  ".join(f"{f}={n}" for f, n in totals.items()) + f"  slop={len(V)}")
    print("note\tcontradiction (fit MUS) and redundancy (economy) are not computed: statistical verifier pending")
    return 1 if V else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
