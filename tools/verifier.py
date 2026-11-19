#!/usr/bin/env python3
"""Statistical verifier client (methodology SLP.12-SLP.14). Needs OPENROUTER_API_KEY.

Usage: tools/verifier.py pilot CALIBRATION_JSON N   -> runs the first N items once per model, prints p and cost
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
