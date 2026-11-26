# Next — state and pending decisions (2026-11-25)

State: draft v4 passes every verification defined so far, and a second run gives the same result.
- Mechanical figures: `python3 tools/measure.py docs/glossary.md docs/methodology-draft.md` → slop 0.
- Contradiction (SLP.26): `tools/contradiction.py judge docs/glossary.md docs/methodology-draft.md judgements/contradiction-v4-3x.jsonl` → 0 contradictions, 0 referred, 0 incomplete.
- Redundancy (SLP.12, SLP.13, SLP.28): `tools/verifier.py judge … calibration/w5/thresholds.json judgements/redundancy-v4.jsonl`, with escalations resolved by `tools/delegate.py resolve` → 0 defects, 0 escalated, 0 incomplete.
- Tests: `python3 -m unittest discover -s tests`.
Paid checks need `OPENROUTER_API_KEY=$(pi auth print-api-key --provider openrouter)`.

Pending user decisions:
1. Proposals that predate the 2026-11-25 delegation and were not reviewed in it: COM.7, OPN.2, SLP.11, SLP.16, SLP.19, SLP.20, SLP.22, SLP.9, TSK.5. SLP.9, SLP.11 and SLP.19 were edited under the delegation.

Also open:
- SLP.13 judges redundancy element by element; SLP.9 counts economy as |Σ'| minus the smallest equivalent subset. They differ when two elements are redundant with each other.
- Evidence is small: 8 reserved contradiction cases, one run each, without definitions (SLP.27); delegate calibrated in-sample (SLP.29). The C05 label is debatable.
- The contradiction judge varied between compatible and refer in 4 of 27 repeated pairs; the three-run unanimity rule mitigates it but does not remove it.
- Z3 (formal route) runs from /tmp/m-z3, outside the repository.
- `INTENT` and `AGREEMENT` are roots written in prose and are not measured.
- The hold-out corpus at `~/personal/dev/m-holdout/` belongs to the rejected v2 evaluator and is stale.
