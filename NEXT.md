# Next — pending decisions (2026-11-19)

State: draft v3+ passes the mechanical figures (`tools/measure.py`, slop = 0). Contradiction and redundancy are not yet certified: the statistical verifier fails on realistic items (`calibration/w5/`, see CHANGELOG).

Pending user decisions:

1. Retry HTTP 429/503 with backoff in `tools/verifier.py`: a transport failure is neither a vote nor a schema failure.
2. Replace SLP.24/SLP.25 with the overlap-escalating rule: decide yes only above every calibration "no" and at or above the lowest "yes"; decide no only below every "yes" and at or below the highest "no"; escalate the rest. Offline numbers: redundancy passes with perplexity and gemini (4/22 escalated); contradiction passes with no model.
3. Contradiction: (a) reasoning chat models as typed judges, calibrated the same way; (b) the formal route (SLP.11) with a logic reasoner; or both, compared.

Also open:
- Validation halves have 22 items per question; "zero wrong" there is weak evidence.
- Labels XC7 and XC8 are debatable; they were not changed after seeing results.
- `INTENT` and `AGREEMENT` are roots written in prose and are not measured.
- The hold-out corpus at `~/personal/dev/m-holdout/` belongs to the rejected v2 evaluator and is stale.
