# Communication agreement

Base agreement for developing the methodology in `docs/methodology-draft.md`. It is monitored and verified like any other artefact; when a verification fails, it is reviewed and updated.

- **Language**: conversation in Spanish, documents in English. New terms go into the draft's glossary.
- **Channels**: the conversation and the files in this repository. Anything not written here is not agreed.
- **Format**: one topic per iteration. The agent proposes a concrete change to the draft; the user validates or corrects it; then it is applied.
- **Moments**: each closed iteration bumps the draft version (v0 → v1 …) and adds a line to `CHANGELOG.md`.
- **Commitments**:
  - Validated content is not changed without agreement.
  - Agent contributions are marked **(proposal)** until validated.
  - Merging a pull request into `main` validates all proposals present in the merged draft and glossary. GitHub Actions removes their `status: proposal` metadata and version-heading label in a follow-up commit; historical records are not rewritten. Closing a pull request without merging does not validate it.
- **Exceptions**: a contradiction with the intent stops the work and is raised in three lines (Drift / Intent says / Reject or amend the intent?), following the `work-intent` skill.

## History
- 2026-11-26: the user defined merging a pull request as acceptance of its proposals; post-merge cleanup is automated with GitHub Actions.
- 2026-11-18: agreement validated by the user.
- 2026-11-25: the user delegated decisions to the agent until the conditions for the first iteration hold ("toma tú las decisiones necesarias o lanza un agente con contexto limpio que decida"). Draft changes made under the delegation are marked `status: proposal` and await the user's validation.
