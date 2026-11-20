#!/usr/bin/env python3
"""Statistical verifier client (methodology SLP.12-SLP.14). Needs OPENROUTER_API_KEY.

Usage: tools/verifier.py pilot CALIBRATION_JSON N   -> runs the first N items once per model, prints p and cost
       tools/verifier.py check CALIBRATION_JSON OUT_DIR -> recompute thresholds and validation from results.jsonl
       tools/verifier.py judge GLOSSARY DOC THRESHOLDS_JSON RECORD_JSONL -> SLP.12-14 over a document
       tools/verifier.py calibrate CALIBRATION_JSON OUT_DIR MODELS RUNS -> calibrate on split cal, check on split val
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
    """SLP.24: per (question, model), tau_yes = min p over 'yes' items, tau_no = max p over 'no' items."""
    out = {}
    for r in rows:
        if r.get("void"):
            continue
        t = out.setdefault(f"{r['kind']}|{r['model']}", {"tau_yes": 1.0, "tau_no": 0.0, "failures": 0})
        if r["p"] is None:
            t["failures"] += 1
        elif r["label"]:
            t["tau_yes"] = min(t["tau_yes"], r["p"])
        else:
            t["tau_no"] = max(t["tau_no"], r["p"])
    for t in out.values():
        t["passes"] = t["tau_no"] < t["tau_yes"] and t["failures"] == 0
    return out


def decide(ps, t):
    """SLP.13: every run at least tau_yes -> True, every run at most tau_no -> False, otherwise None (escalate)."""
    if all(p >= t["tau_yes"] for p in ps):
        return True
    if all(p <= t["tau_no"] for p in ps):
        return False
    return None


def validate(rows, th):
    """SLP.25: per (question, model), count wrong and escalated decisions per item over its runs."""
    items = {}
    for r in rows:
        if r.get("void"):
            continue
        items.setdefault((f"{r['kind']}|{r['model']}", r["id"], r["label"]), []).append(r["p"])
    out = {}
    for (key, _id, label), ps in items.items():
        v = out.setdefault(key, {"wrong": 0, "escalated": 0, "failures": 0, "deterministic": True, "wrong_ids": []})
        if None in ps:
            v["failures"] += 1
            continue
        v["deterministic"] &= len(set(ps)) == 1
        d = decide(ps, th[key])
        if d is None:
            v["escalated"] += 1
        elif d != label:
            v["wrong"] += 1
            v["wrong_ids"].append(_id)
    for v in out.values():
        v["passes"] = v["wrong"] == 0 and v["failures"] == 0
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

if __name__ == "__main__" and sys.argv[1:2] == ["check"]:
    from pathlib import Path
    cal, out = json.load(open(sys.argv[2])), Path(sys.argv[3])
    void = {i["id"] for k in cal for i in cal[k] if i.get("void")}
    rows = [dict(json.loads(line), void=False) for line in (out / "results.jsonl").read_text().splitlines()]
    for r in rows:
        r["void"] = r["id"] in void
    th = thresholds([r for r in rows if r["split"] == "cal"])
    val = validate([r for r in rows if r["split"] == "val"], th)
    (out / "thresholds.json").write_text(json.dumps(th, indent=2, sort_keys=True) + "\n")
    (out / "validation.json").write_text(json.dumps(val, indent=2, sort_keys=True) + "\n")
    for key in sorted(th):
        print(f"{key}\tcal={'pass' if th[key]['passes'] else 'FAIL'}\tval={'pass' if val[key]['passes'] else 'FAIL'}"
              f"\twrong={val[key]['wrong_ids']}\tescalated={val[key]['escalated']}")

if __name__ == "__main__" and sys.argv[1:2] == ["calibrate"]:
    from concurrent.futures import ThreadPoolExecutor
    from pathlib import Path
    cal, out = json.load(open(sys.argv[2])), Path(sys.argv[3])
    models, runs = sys.argv[4].split(","), int(sys.argv[5])
    jobs = [(kind, item, model, run) for kind in ("contradiction", "redundancy") for item in cal[kind]
            for model in models for run in range(runs)]

    def one(job):
        kind, item, model, run = job
        row = {"kind": kind, "id": item["id"], "label": item["label"], "split": item["split"], "model": model,
               "run": run, "template": TEMPLATE_HASH, "p": None, "cost": 0.0, "served": None}
        try:
            row["p"], row["cost"], row["served"] = ask(model, kind, state_of(kind, item))
        except Exception as exc:  # SLP.13: a failure, not a vote
            row["error"] = repr(exc)
        return row

    with ThreadPoolExecutor(16) as pool:
        rows = list(pool.map(one, jobs))
    (out / "results.jsonl").write_text("".join(json.dumps(r) + "\n" for r in rows))
    th = thresholds([r for r in rows if r["split"] == "cal"])
    val = validate([r for r in rows if r["split"] == "val"], th)
    (out / "thresholds.json").write_text(json.dumps(th, indent=2, sort_keys=True) + "\n")
    (out / "validation.json").write_text(json.dumps(val, indent=2, sort_keys=True) + "\n")
    for key in sorted(th):
        t, v = th[key], val.get(key, {})
        print(f"{key}\ttau_yes={t['tau_yes']:.2f}\ttau_no={t['tau_no']:.2f}\tcal={'pass' if t['passes'] else 'FAIL'}"
              f"\tval_wrong={v.get('wrong')}\tval_escalated={v.get('escalated')}\tval_failures={v.get('failures')}"
              f"\tdeterministic={v.get('deterministic')}")
    print(f"calls\t{len(rows)}\tcost_usd\t{sum(r['cost'] for r in rows):.6f}")

PANELS = {  # SLP.12: model -> runs (1 when its output repeats exactly)
    "contradiction": {"microsoft/microsoft-decision-1.1": 1, "google/gemini-decision-1": 1},
    "redundancy": {"microsoft/microsoft-decision-1.1": 1, "perplexity/pplx-decider-v1.2": 3, "typesafe/jev-1.14": 3},
}

if __name__ == "__main__" and sys.argv[1:2] == ["judge"]:
    # tools/verifier.py judge GLOSSARY DOC THRESHOLDS_JSON RECORD_JSONL
    from concurrent.futures import ThreadPoolExecutor
    from itertools import combinations
    from pathlib import Path
    import measure

    glossary, doc, th_path, record = (Path(a) for a in sys.argv[2:6])
    th = json.loads(th_path.read_text())
    variants = {}
    for e in measure.parse(glossary, []):
        for v in e["meta"].get("variants", "").split(","):
            if v.strip():
                variants[v.strip().lower()] = e["meta"]["defines"]
    els = [e for e in measure.parse(doc, []) if e["kind"] != "definition"]
    for e in els:
        e["uses"] = {variants[u.strip().lower()] for u in measure.MARK.findall(e["text"]) if u.strip().lower() in variants}
        e["plain"] = measure.MARK.sub(r"\1", e["text"])
    tasks = [("contradiction", (a["id"], b["id"]), {"a": a["plain"], "b": b["plain"]})
             for a, b in combinations(els, 2) if a["uses"] & b["uses"]]
    for e in els:
        ctx = [o for o in els if o is not e and o["uses"] & e["uses"]]
        if ctx:
            tasks.append(("redundancy", (e["id"],), {"target": e["plain"], "context": [o["plain"] for o in ctx]}))

    old = {}
    if record.exists():
        for line in record.read_text().splitlines():
            j = json.loads(line)
            old[(j["kind"], j["input_hash"], j["template"])] = j

    def judge_one(task):
        kind, ids, state = task
        h = hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]
        if (kind, h, TEMPLATE_HASH) in old:  # SLP.14: judged again only when a hash changes
            return old[(kind, h, TEMPLATE_HASH)]
        ps, cost, failures = {}, 0.0, 0
        for model, runs in PANELS[kind].items():
            ps[model] = []
            for _ in range(runs):
                try:
                    p, c, _served = ask(model, kind, state)
                    ps[model].append(p)
                    cost += c
                except Exception:
                    failures += 1
        votes = [decide(v, th[f"{kind}|{m}"]) for m, v in ps.items()]
        decision = None if failures else (True if all(v is True for v in votes) else
                                           False if all(v is False for v in votes) else None)
        return {"kind": kind, "ids": list(ids), "input_hash": h, "template": TEMPLATE_HASH,
                "panel": PANELS[kind], "ps": ps, "failures": failures, "decision": decision, "cost": cost}

    with ThreadPoolExecutor(16) as pool:
        results = list(pool.map(judge_one, tasks))
    record.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in results))
    for kind in ("contradiction", "redundancy"):
        rs = [r for r in results if r["kind"] == kind]
        print(f"{kind}\tjudged={len(rs)}\tdefect={sum(r['decision'] is True for r in rs)}"
              f"\tclean={sum(r['decision'] is False for r in rs)}\tescalated={sum(r['decision'] is None for r in rs)}")
        for r in rs:
            if r["decision"] is not False:
                print(f"  {'DEFECT' if r['decision'] else 'ESCALATE'}\t{','.join(r['ids'])}\t"
                      + " ".join(f"{m.split('/')[1][:12]}={[round(p, 2) for p in v]}" for m, v in r["ps"].items()))
    print(f"cost_usd\t{sum(r['cost'] for r in results):.6f}")
