# Changelog

- 2026-11-18 — v0: initial draft; project created; communication agreement validated.
- 2026-11-19 — v1: intent established (.hermes/intent/project.md); slop figures validated; measurement, tooling and evaluation plan added.
- 2026-11-19 — v2: glossary; fixed evaluator (eval/: clean and seeded corpus of section 2, truth, vague-word list, counting conventions); hold-out corpus kept outside the repository.
- 2026-11-19 — v2 evaluator rejected (review w3: not ready). Decisions: draft first; structured elements; pure-formula counting (a defect counts in every figure it breaks); truth, clean corpus and hold-out isolated from evaluated agents.
- 2026-11-19 — v3: glossary and draft rewritten as structured elements; tools/measure.py computes the mechanical figures (all 0); rejected eval/ removed; vague-word and Spanish stopword lists in docs/lists/.
- 2026-11-19 — calibration run (200 calls, 0.0035 USD): jev-1.14 passes both questions; gpt-6-luna-decisions fails both (SLP.24).
- 2026-11-19 — calibration+validation of 6 decision models (1440 calls, 0.0153 USD). SLP.13/SLP.24 threshold definitions swapped to remove a self-contradiction (proposal).
- 2026-11-19 — realistic calibration: items by w5 (gpt-6.2-sol), labels by w7 (4 independent agents); 6 models, 1728 calls, 0.0255 USD: no model passes SLP.24/25 on either question. judge cache now re-decides stored probabilities with current thresholds.
