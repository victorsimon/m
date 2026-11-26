#!/usr/bin/env python3
"""Contradiction methods compared under decision 3: a text judge and a formal translation checked by Z3.

Usage: tools/contradiction.py run PROMPT_DIR CASES_JSON OUT_JSONL MODEL Z3_PATH   (needs OPENROUTER_API_KEY)
       tools/contradiction.py score OUT_JSONL LABELS_JSON
       tools/contradiction.py judge GLOSSARY DOC RECORD_JSONL [--dry-run]   -> SLP.26 over a document (exit 1 unless complete)
CASES_JSON is a list of {id, a, b}; only a and b reach the model, one pair per request.
LABELS_JSON maps id -> {contradiction: bool}. Every verdict is contradiction, compatible, refer or invalid.
"""
import json
import os
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

URL = "https://openrouter.ai/api/v1/chat/completions"
ALLOWED = {"set-logic", "declare-sort", "declare-fun", "declare-const", "define-sort", "define-fun", "assert"}


def commands(smt2):
    """Top-level command heads, skipping comments, strings and |quoted| symbols. Raises on unbalanced input."""
    heads, depth, i, n = [], 0, 0, len(smt2)
    while i < n:
        ch = smt2[i]
        if ch == ";":
            while i < n and smt2[i] != "\n":
                i += 1
        elif ch in "\"|":
            j = smt2.find(ch, i + 1)
            while ch == '"' and j != -1 and smt2[j + 1:j + 2] == '"':  # "" escapes a quote in SMT-LIB 2.6
                j = smt2.find(ch, j + 2)
            if j == -1:
                raise ValueError("unterminated literal")
            i = j
        elif ch == "(":
            if depth == 0:
                heads.append(re.match(r"\(\s*([^\s()]*)", smt2[i:]).group(1))
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("unbalanced parentheses")
        elif depth == 0 and not ch.isspace():
            raise ValueError("text outside a command")
        i += 1
    if depth:
        raise ValueError("unbalanced parentheses")
    return heads


def formal_problem(reply):
    """None when a formal reply may go to the solver, otherwise the reason it is invalid."""
    if reply.get("status") != "encoded":
        return None if reply.get("status") == "refer" else "status is neither encoded nor refer"
    smt2, clauses = reply.get("smt2"), reply.get("clauses")
    if not isinstance(smt2, str) or not isinstance(clauses, list) or not clauses:
        return "missing smt2 or clauses"
    try:
        heads = commands(smt2)
    except ValueError as exc:
        return str(exc)
    if set(heads) - ALLOWED:
        return f"forbidden commands {sorted(set(heads) - ALLOWED)}"
    if heads.count("assert") != len(re.findall(r":named\s", smt2)):
        return "an assertion is not named"
    named = re.findall(r":named\s+([^\s()]+)", smt2)
    listed = [a for c in clauses for a in c.get("assertions", [])]
    if len(set(named)) != len(named) or sorted(named) != sorted(listed):
        return "named assertions and clause mapping differ"
    if {c.get("source") for c in clauses} != {"a", "b"}:
        return "clauses do not cover both statements"
    return None


def z3_verdict(output):
    """(verdict, evidence) from Z3 output; any error or other answer is invalid, never a semantic verdict."""
    lines = output.strip().splitlines()
    if not lines or "(error" in output or lines[0] not in ("sat", "unsat"):
        return "invalid", output[:2000]
    return ("compatible" if lines[0] == "sat" else "contradiction"), "\n".join(lines[1:])


def solve(z3, smt2):
    header = "(set-option :produce-unsat-cores true)\n(set-option :produce-models true)\n"
    runs = []
    for _ in range(2):  # the same check twice must agree
        first = subprocess.run([z3, "-in", "-T:20"], input=header + smt2 + "\n(check-sat)\n",
                               text=True, capture_output=True, timeout=40).stdout
        extra = {"sat": "(get-model)", "unsat": "(get-unsat-core)"}.get(first.strip(), "")
        runs.append(subprocess.run([z3, "-in", "-T:20"], input=header + smt2 + f"\n(check-sat)\n{extra}\n",
                                   text=True, capture_output=True, timeout=40).stdout)
    if runs[0] != runs[1]:
        return "invalid", "solver output differs between runs"
    return z3_verdict(runs[0])


def ask(model, system, pair):
    body = {"model": model, "temperature": 0, "max_tokens": 4000, "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": json.dumps(pair)}]}
    req = urllib.request.Request(URL, json.dumps(body).encode(), {
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"], "Content-Type": "application/json"})
    from verifier import urlopen_retry
    with urlopen_retry(req, 300) as r:
        return body, json.load(r)


def judge(method, reply, z3):
    if method == "text":
        ok = reply.get("decision") in ("compatible", "contradiction", "refer") and isinstance(reply.get("evidence"), str)
        return (reply["decision"], reply["evidence"]) if ok else ("invalid", "text reply fails the schema")
    problem = formal_problem(reply)
    if problem:
        return "invalid", problem
    return ("refer", reply.get("note", "")) if reply["status"] == "refer" else solve(z3, reply["smt2"])


def score(rows, labels):
    out = {}
    for r in rows:
        s = out.setdefault(r["method"], {"correct": 0, "wrong": 0, "refer": 0, "invalid": 0, "wrong_ids": []})
        if r["verdict"] in ("refer", "invalid"):
            s[r["verdict"]] += 1
        elif (r["verdict"] == "contradiction") == labels[r["id"]]["contradiction"]:
            s["correct"] += 1
        else:
            s["wrong"] += 1
            s["wrong_ids"].append(r["id"])
    for s in out.values():
        s["passes"] = s["wrong"] == 0 and s["invalid"] == 0
    return out


if __name__ == "__main__" and sys.argv[1:2] == ["run"]:
    from pathlib import Path
    prompts, cases, out, model, z3 = Path(sys.argv[2]), json.loads(Path(sys.argv[3]).read_text()), Path(sys.argv[4]), sys.argv[5], sys.argv[6]
    subprocess.run(["shasum", "-a", "256", "-c", "SHA256SUMS"], cwd=prompts, check=True, capture_output=True)
    total = 0.0
    for case in cases:
        for method in ("text", "formal"):
            body, ans = ask(model, (prompts / f"{method}.txt").read_text(), {"a": case["a"], "b": case["b"]})
            total += ans["usage"]["cost"]
            try:
                verdict, evidence = judge(method, json.loads(ans["choices"][0]["message"]["content"]), z3)
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
                verdict, evidence = "invalid", f"reply fails the schema: {exc!r}"
            row = {"id": case["id"], "method": method, "verdict": verdict, "evidence": evidence,
                   "served": ans.get("model"), "cost": ans["usage"]["cost"], "request": body, "response": ans}
            with out.open("a") as f:
                f.write(json.dumps(row) + "\n")
            print(f"{case['id']}\t{method}\t{verdict}\t{ans.get('model')}\t{ans['usage']['cost']}", flush=True)
    print(f"cost_usd\t{total:.6f}")

MODEL = "anthropic/claude-opus-5.5"  # SLP.26
TEMPLATE = Path(__file__).resolve().parent.parent / "calibration" / "contradiction-v2" / "text.txt"
TEMPLATE_SHA256 = "87d3e0222e7398b266acb7e53c4c2f87de7a6901ebfc41c6cc8f9f7330c6b34c"


RUNS = 3  # SLP.26


def aggregate(verdicts):
    """SLP.26: contradiction or compatible only when all RUNS replies agree; refer otherwise; incomplete if short."""
    if len(verdicts) < RUNS:
        return "incomplete"
    return verdicts[0] if len(set(verdicts)) == 1 and verdicts[0] != "refer" else "refer"


def pairs(els):
    """SLP.26: every pair of elements that share a term."""
    from itertools import combinations
    return [(a, b) for a, b in combinations(els, 2) if a["uses"] & b["uses"]]


if __name__ == "__main__" and sys.argv[1:2] == ["judge"]:
    import hashlib
    from concurrent.futures import ThreadPoolExecutor
    from verifier import definitions, elements
    glossary, doc, record = (Path(a) for a in sys.argv[2:5])
    template = TEMPLATE.read_text()
    if hashlib.sha256(template.encode()).hexdigest() != TEMPLATE_SHA256:
        sys.exit("template hash differs from SLP.26")
    todo = pairs(elements(glossary, doc))
    print(f"pairs\t{len(todo)}")
    if "--dry-run" in sys.argv:
        sys.exit(0)
    old = {}
    if record.exists():  # SLP.14: judge again only when a hash changes
        for line in record.read_text().splitlines():
            j = json.loads(line)
            runs = j.get("runs") or ([{"verdict": j["verdict"], "evidence": j["evidence"]}]
                                     if j.get("verdict") in ("contradiction", "compatible", "refer") else [])
            old.setdefault((j["input_hash"], j["template"], j["model"]), []).extend(runs)

    def one(pair):
        a, b = pair
        state = {"a": a["plain"], "b": b["plain"], "definitions": definitions(glossary, a["uses"] | b["uses"])}
        h = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]
        row = {"ids": [a["id"], b["id"]], "input_hash": h, "template": TEMPLATE_SHA256[:12], "model": MODEL, "cost": 0.0}
        runs, problem = old.get((h, row["template"], MODEL), [])[:RUNS], ""  # SLP.14: reuse recorded runs
        while len(runs) < RUNS and not problem:
            try:
                _body, ans = ask(MODEL, template, state)
                row["cost"] += ans["usage"]["cost"]
                verdict, evidence = judge("text", json.loads(ans["choices"][0]["message"]["content"]), None)
            except (json.JSONDecodeError, KeyError, TypeError, AttributeError) as exc:
                verdict, evidence = "invalid", f"reply fails the schema: {exc!r}"
            except Exception as exc:  # SLP.26: transport failure leaves the verification incomplete
                verdict, evidence = "invalid", f"transport: {exc!r}"
            if verdict == "invalid":
                problem = evidence
            else:
                runs.append({"verdict": verdict, "evidence": evidence})
        row["runs"], row["verdict"] = runs, aggregate([r["verdict"] for r in runs])
        row["evidence"] = problem or next((r["evidence"] for r in runs if r["verdict"] != "compatible"), runs[0]["evidence"])
        return row

    with ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(one, todo))
    record.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows))
    counts = {v: sum(r["verdict"] == v for r in rows) for v in ("contradiction", "compatible", "refer", "incomplete")}
    print("\t".join(f"{k}={v}" for k, v in counts.items()))
    for r in rows:
        if r["verdict"] != "compatible":
            print(f"  {r['verdict'].upper()}\t{','.join(r['ids'])}\t{r['evidence'][:200]}")
    print(f"cost_usd\t{sum(r['cost'] for r in rows):.6f}")
    sys.exit(1 if counts["incomplete"] else 0)

if __name__ == "__main__" and sys.argv[1:2] == ["score"]:
    rows = [json.loads(line) for line in open(sys.argv[2])]
    print(json.dumps(score(rows, json.load(open(sys.argv[3]))), indent=2, sort_keys=True))
