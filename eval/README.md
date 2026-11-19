# Evaluator

Fixed evaluator for slop-measurement candidates (see `docs/methodology-draft.md` §7, Evaluation plan). Evaluated agents must not modify anything in this directory.

## Corpus

- `corpus/clean.md` — section 2 of the draft, made impeccable. True Slop = 0.
- `corpus/seeded.md` — the same section with seeded defects. True counts in `corpus/truth.tsv`.
- A hold-out corpus exists outside this repository and is not shown to evaluated agents.

True counts for `seeded.md`: form 2, fit 2, economy 1, completeness 1, order 1, sharpness 2, truthfulness 1 (total 10).

## Counting conventions

These conventions are recorded judgement; they make the true counts deterministic.

1. An element is a bracketed block `[XXX.n]`. Defects are located by element id.
2. A term is a concept of the methodology. Ordinary vocabulary is not a term.
3. A misnamed glossary term counts as **form** only, not as completeness.
4. An element in the wrong language counts as **form** only.
5. Each minimal unsatisfiable subset counts as one **fit** violation.
6. **Order** counts a use of a term before its definition inside the same artefact; terms defined only in the glossary have no position.
7. **Sharpness** counts each occurrence of an entry of `vague-words.txt`, and each term with more than one definition.
8. **Truthfulness** counts empirical claims without evidence. Prescriptive rules are not claims.

## Metric

Error = Σ over figures of |detected − true|, for each corpus. A candidate passes only with error 0 on every corpus, and the same output on two runs. Ties go to the simpler candidate.
