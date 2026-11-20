#!/usr/bin/env python3
"""Statistical verifier client (methodology SLP.12-SLP.14). Needs OPENROUTER_API_KEY.

Usage: tools/verifier.py pilot CALIBRATION_JSON N   -> runs the first N items once per model, prints p and cost
       tools/verifier.py calibrate CALIBRATION_JSON OUT_DIR -> all items, all runs; writes results.jsonl and thresholds.json
"""
import hashlib
import json
import os
import sys
import urllib.request

URL = "https://openrouter.ai/api/alpha/decisions"
MODELS = {"typesafe/jev-1.14": 3, "openai/gpt-6-luna-decisions": 2}  # runs per model (SLP.12)

QUESTIONS = {
    "contradiction": {
        "type": "noul",
        "instructions": "Do statement a and statement b contradict each other?",
        "criteria": {
            "true": "a and b cannot both hold at the same time.",
            "false": "a and b can both hold at the same time, even if they address different things.",
        },
    },
    "redundancy": {
        "type": "noul",
        "instructions": "Is the target statement already implied by the context statements?",
        "criteria": {
            "true": "Everything the target says follows from the context; removing the target loses nothing.",
            "false": "The target says at least one thing the context does not.",
        },
    },
}
TEMPLATE_HASH = hashlib.sha256(json.dumps(QUESTIONS, sort_keys=True).encode()).hexdigest()[:12]


def ask(model, kind, state):
    """One run. Returns (p, cost_usd, served_model). Raises on a response that fails the schema (SLP.13: failure, not a vote)."""
    body = json.dumps({"model": model, "state": state, "questions": {"q": QUESTIONS[kind]}}).encode()
    req = urllib.request.Request(URL, body, {
        "Authorization": "Bearer " + os.environ["OPENROUTER_API_KEY"],
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.load(r)
    answer = data["answers"]["q"]
    p = answer["noul"]
    if not (isinstance(p, (int, float)) and 0 <= p <= 1):
        raise ValueError(f"schema failure: {answer!r}")
    return float(p), float(data["usage"]["cost"]), data["model"]


def thresholds(rows):
    """SLP.24: per (question, model), tau_yes = max p over 'no' items, tau_no = min p over 'yes' items."""
    out = {}
    for r in rows:
        t = out.setdefault(f"{r['kind']}|{r['model']}", {"tau_yes": 0.0, "tau_no": 1.0, "failures": 0})
        if r["p"] is None:
            t["failures"] += 1
        elif r["label"]:
            t["tau_no"] = min(t["tau_no"], r["p"])
        else:
            t["tau_yes"] = max(t["tau_yes"], r["p"])
    for t in out.values():
        t["passes"] = t["tau_yes"] < t["tau_no"] and t["failures"] == 0
    return out


def state_of(kind, item):
    if kind == "contradiction":
        return {"a": item["a"], "b": item["b"]}
    return {"target": item["target"], "context": item["context"]}


if __name__ == "__main__" and sys.argv[1:2] == ["pilot"]:
    cal, n = json.load(open(sys.argv[2])), int(sys.argv[3])
    total = 0.0
    print(f"template {TEMPLATE_HASH}")
    for kind in ("contradiction", "redundancy"):
        for item in cal[kind][:n]:
            for model in MODELS:
                p, cost, served = ask(model, kind, state_of(kind, item))
                total += cost
                print(f"{kind}\t{item['id']}\t{item['label']}\t{model}\t{served}\tp={p:.3f}\tcost={cost:.8f}")
    print(f"total_cost_usd\t{total:.8f}")

if __name__ == "__main__" and sys.argv[1:2] == ["calibrate"]:
    from pathlib import Path
    cal, out = json.load(open(sys.argv[2])), Path(sys.argv[3])
    rows = []
    for kind in ("contradiction", "redundancy"):
        for item in cal[kind]:
            for model, runs in MODELS.items():
                for run in range(runs):
                    row = {"kind": kind, "id": item["id"], "label": item["label"], "model": model,
                           "run": run, "template": TEMPLATE_HASH, "p": None, "cost": 0.0, "served": None}
                    try:
                        row["p"], row["cost"], row["served"] = ask(model, kind, state_of(kind, item))
                    except Exception as exc:  # SLP.13: a failure, not a vote
                        row["error"] = repr(exc)
                    rows.append(row)
    (out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    th = thresholds(rows)
    (out / "thresholds.json").write_text(json.dumps(th, indent=2, sort_keys=True) + "\n")
    print(json.dumps(th, indent=2, sort_keys=True))
    print(f"calls\t{len(rows)}\tcost_usd\t{sum(r['cost'] for r in rows):.6f}")
