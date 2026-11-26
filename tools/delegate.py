#!/usr/bin/env python3
"""Delegate for redundancy escalations (the user delegated escalated decisions on 2026-11-25).

Usage: tools/delegate.py calibrate CALIBRATION_JSON OVERRIDES_JSON OUT_JSONL  -> run on every labelled redundancy item
       tools/delegate.py resolve GLOSSARY DOC RECORD_JSONL                     -> decide items the panel escalated
A decision needs RUNS unanimous replies; anything else is refer (left to the user). Needs OPENROUTER_API_KEY.
Decisions go to judgements/redundancy-decisions.jsonl next to RECORD_JSONL; tools/verifier.py judge applies them.
"""
import hashlib
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from contradiction import ask
from verifier import definitions, input_hash, redundancy_tasks

MODEL = "anthropic/claude-opus-5.5"
RUNS = 3
TEMPLATE = Path(__file__).resolve().parent.parent / "calibration" / "redundancy-delegate-v1" / "text.txt"
TEMPLATE_SHA256 = "bbc5f35dd70b29a78f19e79454c6d86d0e0cc143ed9c81eebc8c74063d82761e"


def aggregate(verdicts):
    """Unanimity over RUNS replies decides; disagreement or any refer is refer; fewer replies is incomplete."""
    if len(verdicts) < RUNS:
        return "incomplete"
    return verdicts[0] if len(set(verdicts)) == 1 else "refer"


def decide(state):
    template = TEMPLATE.read_text()
    if hashlib.sha256(template.encode()).hexdigest() != TEMPLATE_SHA256:
        sys.exit("delegate template hash differs")
    runs = []
    for _ in range(RUNS):
        try:
            _body, ans = ask(MODEL, template, state)
            reply = json.loads(ans["choices"][0]["message"]["content"])
        except Exception as exc:  # transport or schema: incomplete, never a decision
            return "incomplete", runs, repr(exc)
        if reply.get("decision") not in ("redundant", "not_redundant", "refer") or not isinstance(reply.get("evidence"), str):
            return "incomplete", runs, "reply fails the schema"
        runs.append({"decision": reply["decision"], "evidence": reply["evidence"]})
    verdict = aggregate([r["decision"] for r in runs])
    return verdict, runs, next((r["evidence"] for r in runs if r["decision"] != "not_redundant"), runs[0]["evidence"])


if __name__ == "__main__" and sys.argv[1:2] == ["calibrate"]:
    cal, overrides, out = json.load(open(sys.argv[2])), json.load(open(sys.argv[3])), Path(sys.argv[4])
    items = [i for i in cal["redundancy"] if not i.get("void")]

    def one(item):
        label = overrides.get(item["id"], item["label"])
        verdict, runs, _ = decide({"target": item["target"], "context": item["context"]})
        return {"id": item["id"], "label": label, "verdict": verdict, "runs": runs}

    with ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(one, items))
    out.write_text("".join(json.dumps(r) + "\n" for r in rows))
    wrong = [r["id"] for r in rows if r["verdict"] in ("redundant", "not_redundant") and (r["verdict"] == "redundant") != r["label"]]
    print(f"items={len(rows)}\tcorrect={sum(r['verdict'] in ('redundant', 'not_redundant') for r in rows) - len(wrong)}"
          f"\twrong={wrong}\trefer={sum(r['verdict'] == 'refer' for r in rows)}\tincomplete={sum(r['verdict'] == 'incomplete' for r in rows)}")
    sys.exit(1 if wrong or any(r["verdict"] == "incomplete" for r in rows) else 0)

if __name__ == "__main__" and sys.argv[1:2] == ["resolve"]:
    glossary, doc, record = (Path(a) for a in sys.argv[2:5])
    escalated = {r["input_hash"] for r in map(json.loads, record.read_text().splitlines())
                 if r["complete"] and r["decision"] is None and not r.get("delegated")}
    dec_path = record.parent / "redundancy-decisions.jsonl"
    known = {json.loads(line)["input_hash"] for line in dec_path.read_text().splitlines()} if dec_path.exists() else set()
    todo = [t for t in redundancy_tasks(glossary, doc) if input_hash(t[2]) in escalated - known]
    els = {}

    def one(task):
        _kind, ids, state = task
        verdict, runs, evidence = decide(state)
        return {"ids": list(ids), "input_hash": input_hash(state), "decision": verdict, "evidence": evidence,
                "runs": runs, "template": TEMPLATE_SHA256[:12], "decider": f"delegate {MODEL} x{RUNS} temperature 0"}

    with ThreadPoolExecutor(8) as pool:
        rows = list(pool.map(one, todo))
    with dec_path.open("a") as f:
        f.writelines(json.dumps(r, sort_keys=True) + "\n" for r in rows if r["decision"] != "incomplete")
    for r in rows:
        print(f"{r['decision']}\t{','.join(r['ids'])}\t{r['evidence'][:160]}")
