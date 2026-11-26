# Next — state and pending decisions (2026-11-25)

State: draft v4 passes every verification defined so far, and a second run gives the same result.
- Mechanical figures: `python3 tools/measure.py docs/glossary.md docs/methodology-draft.md` → slop 0.
- Contradiction (SLP.26): `tools/contradiction.py judge docs/glossary.md docs/methodology-draft.md judgements/contradiction-v4-3x.jsonl` → 0 contradictions, 0 referred, 0 incomplete.
- Redundancy (SLP.12, SLP.13, SLP.28): `tools/verifier.py judge … calibration/w5/thresholds.json judgements/redundancy-v4.jsonl`, with escalations resolved by `tools/delegate.py resolve` → 0 defects, 0 escalated, 0 incomplete.
- Tests: `python3 -m unittest discover -s tests`.
Paid checks need `OPENROUTER_API_KEY=$(pi auth print-api-key --provider openrouter)`.

Pending user decisions:
1. Validate the changes made under delegation (every element with `status: proposal` added or changed on 2026-11-25; see CHANGELOG). The SLP.3 table lost its third column, a stronger step than the validated alignment with SLP.9.
2. Removed or merged elements: COM.1 (into STR.2 and COM.4), INT.1 and INT.3 (into INT.2), SLP.2 (into SLP.3).
3. Agent override recorded in judgements/redundancy-decisions.jsonl (SLP.2, now lapsed with its removal): confirm whether agent decisions should keep that power.

Also open:
- Whether and how to count "a task without verification", removed from SLP.3 because SLP.9 never counts it.
- SLP.13 judges redundancy element by element; SLP.9 counts economy as |Σ'| minus the smallest equivalent subset. They differ when two elements are redundant with each other.
- Evidence is small: 8 reserved contradiction cases, one run each, without definitions (SLP.27); delegate calibrated in-sample (SLP.29). The C05 label is debatable.
- The contradiction judge varied between compatible and refer in 4 of 27 repeated pairs; the three-run unanimity rule mitigates it but does not remove it.
- Z3 (formal route) runs from /tmp/m-z3, outside the repository.
- `INTENT` and `AGREEMENT` are roots written in prose and are not measured.
- The hold-out corpus at `~/personal/dev/m-holdout/` belongs to the rejected v2 evaluator and is stale.
