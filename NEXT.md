# Next — state and pending decisions (2026-11-26)

State: draft v5 (status: proposal) passes every verification defined so far, and a second run gives the same result. The baseline v4 was checked before any repository edit and passed all four checks (21 tests).
- Mechanical figures: `python3 tools/measure.py docs/glossary.md docs/methodology-draft.md` → slop 0.
- Contradiction (SLP.26): `tools/contradiction.py judge docs/glossary.md docs/methodology-draft.md judgements/contradiction-v5-3x.jsonl` → 0 contradictions, 0 referred, 0 incomplete.
- Redundancy (SLP.12, SLP.13, SLP.28): `python3 tools/verifier.py judge docs/glossary.md docs/methodology-draft.md calibration/w5/thresholds.json judgements/redundancy-v5.jsonl` → 57 clean elements, economy 0, 0 defects, 0 escalated, 0 incomplete (27 by delegate). Escalations: `python3 tools/delegate.py resolve docs/glossary.md docs/methodology-draft.md judgements/redundancy-v5.jsonl`, then run the verifier again to apply decisions.
- Tests: `python3 -m unittest discover -s tests` → 27 pass: the 22 v5 tests, including two mutually redundant elements counted as two by the real CLI without model calls, plus five proposal-cleanup tests.
- Repeat all four checks against the same artefacts and judgement records; compare counts, decisions, completeness and exit codes (not elapsed test time or per-invocation cost). SLP.14 reuses recorded judgements; this is not an independent re-sampling of the models.
Paid checks need `OPENROUTER_API_KEY=$(pi auth print-api-key --provider openrouter)`.

Pending user validation until PR #1 is merged: v5 version label and the draft elements marked `status: proposal`, SLP.9 and SLP.13. GLO.42 in the glossary also retains a pre-existing proposal marker; merging the draft and glossary accepts that proposal too. Proposed definition: count each independently redundant element, retaining every other element in its context; two mutually redundant elements count as two, not as one removable element. The agent adopted the clean-context agent's recommendation; no other draft content changed.

## Merge acceptance automation

- `.github/workflows/accept-proposals.yml` runs only after a PR is merged into `main`, including PRs from forks. It uses `GITHUB_TOKEN` with `contents: write`, not a personal token or deploy key, and checks out the merged commit, never an unmerged PR head.
- `tools/accept_proposals.py` removes proposal metadata from element headers and the version-heading label in `docs/methodology-draft.md` and `docs/glossary.md`. Body text and historical records, including this snapshot and `CHANGELOG.md`, remain unchanged.
- The workflow runs tests and mechanical measurement before committing. Marker removal does not alter element text or semantic judgement inputs. It does not call paid models.
- Deployment requires the workflow to be on upstream `main` and repository rules to allow the Actions token to push the follow-up commit. If a cleanup commit is needed and `main` has advanced after the merged commit, its push fails safely rather than overwriting later changes; resolve against the new branch state before accepting additional markers. When the merged snapshot has no markers to remove, the job succeeds without pushing.
- The workflow has not yet been exercised on GitHub. All 27 local tests pass. A cleaned temporary snapshot passes the full verification suite twice with identical results (slop 0, 347 compatible pairs, 57 clean elements); its semantic judgement inputs are unchanged. Local Git integration exercised the exact workflow commit step: successful push, idempotent no-op, and concurrent-advance rejection with the remote unchanged. Workflow YAML and merged-event/security guards were checked locally.

Also open:
- `tools/contradiction.py judge` exits nonzero only for incomplete checks, not for contradictions or referrals; inspect all reported counts before certifying a state. Repairing its exit-code contract is outside this iteration.
- `workflow_agent` could not load `@earendil-works/pi-coding-agent` in this environment. Clean-context recommendation and review used separate ephemeral Pi CLI processes with only read-only tools and no extensions, MCP, skills or conversation history.
- Evidence is small: 8 reserved contradiction cases, one run each, without definitions (SLP.27); delegate calibrated in-sample (SLP.29). The C05 label is debatable.
- The contradiction judge varied between compatible and refer in 4 of 27 repeated pairs; the three-run unanimity rule mitigates it but does not remove it.
- Z3 (formal route) runs from /tmp/m-z3, outside the repository.
- `INTENT` and `AGREEMENT` are roots written in prose and are not measured.
- The hold-out corpus at `~/personal/dev/m-holdout/` belongs to the rejected v2 evaluator and is stale.
