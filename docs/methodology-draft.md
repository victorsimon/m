# Task-resolution methodology — draft v2

> Status: conceptual draft. Deliberately high level of abstraction; not yet grounded in any harness or tool.
> Items marked **(proposal)** are not validated yet.
> Glossary: `docs/glossary.md`.

## 0. Purpose

Establish a task-resolution methodology that applies at any scale: a single agent, an agent ecosystem, a company, a group of companies.

**Scale invariance principle:** a concept that only makes sense at one scale is either redundant or badly framed.

**Self-application principle:** the methodology also applies to itself and to its own agreements; no piece is exempt.

## 1. Structure

```
            Intent  (distilled per level)
   ┌───────────┬─────────────┬───────────┐
   │   Tasks   │  Capability │  Quality  │
   └───────────┴─────────────┴───────────┘
   ═════ Communication (base agreement) ═════
```

- **Communication**: the substrate. It is the base agreement on which everything else is built.
- **Intent**: above everything. It gives meaning to everything else.
- **Tasks**: the problem.
- **Capability**: the means to solve it.
- **Quality**: the judgement, that is, what is pursued, achieved and applied.

## 2. Communication — the base agreement

It is cross-cutting and foundational. It is understood as the medium, not just a channel. It is the first thing agreed when any working group forms.

Components of the agreement:

- **Language**: shared language and vocabulary (glossary).
- **Channels**: where information flows.
- **Format**: the shape of exchanges.
- **Moments**: when communication happens (milestones, cadence, checkpoints).
- **Commitments**: what is promised for delivery and how delivery is recognised.
- **Exceptions**: what to do when something does not fit the agreement.

Everything else is communication:

| Concept | As communication |
|---|---|
| Distilling intent | downward |
| Verifying or reporting a result | upward |
| Consulting another | lateral |
| Written know-how | deferred in time |
| Regulation | an already-made judgement, communicated |

The agreement **is monitored and verified like anything else**. It does not expire with time or use. When it fails a verification, it is reviewed and, if needed, updated.

Properties of a communication **(proposal)**: fidelity, shared language, direction, timing (immediate or deferred) and recipient (person, agent or environment).

## 3. Intent

- It is set **at each level**.
- It is **inherited non-strictly**: each level's intent complements the one above in order to fulfil it.
- It is **distilled** from level to level: at each step something is lost, something is added and something is translated.
- Verification checks that the result fulfils the intent of its level, and also that this intent still serves the one above.
- Risk of **drift**: small deviations at each distillation can end up emptying the original intent of meaning.

## 4. Tasks

A task is, among other things, a problem.

- **Definition**: on request, out of need, or for maintenance (the environment is alive).
- **Organisation**: decomposition, dependencies, prioritisation and classification.
- **Management**: execution, verification and measurement.

**Decomposition is the methodology**: a way of thinking for solving problems. It also makes the methodology recursive: a task decomposes into tasks, and each one again has its own intent, capability and quality.

Decomposing and delegating forms a new group, so at each level the communication agreement must be inherited or renegotiated. The usual case would be to inherit the base (language, channels) and adjust the local parts (moments, commitments, exceptions) **(proposal)**.

**Autonomy**: a goal of each task, not a standard or a whole. Its boundary is set by the agreement's exceptions.

## 5. Capability

### Intrinsic (the executor's own)
- **Power**: the executor and the effort it applies.
- **Speed**: how much can be done in parallel.
- **Context management**: what the executor has in mind at each moment.

### Extrinsic (lives outside the executor)
This is know-how. Analogy: the person is the model; documents, courses and regulations are the know-how, and they belong to the organisation.

- **Written know-how**:
  - *Descriptive*: how things are (documentation, glossary).
  - *Procedural*: how things are done (courses, methods).
  - *Normative*: what must and must not be done (regulation). It does not extend capability, it limits it, and it connects directly with Quality.
- **Embodied know-how, or consulting another**: borrowing another's judgement, not just their information.

Consequences of know-how living outside: it has to be retrieved, it can grow with what is learned, and it can be reused even when the executor changes.

**Learning**: the environment is alive, so know-how is not only accumulated; it is also reviewed and retired when it stops being valid.

Reference: tacit versus explicit knowledge (Polanyi, Nonaka).

## 6. Quality

It is the concept to pursue, achieve and apply. It is the foundation from which these derive:

- **Constraints**, as a consequence of the quality judgement.
- **Verification and monitoring**, as the application of that judgement: verification is point-in-time, monitoring is continuous.

Attributes: fitness for purpose, verifiability, performance, security, resilience and maintainability.

### Graded verification

Verification does not return a yes or no, but a **diagnosis** with these dimensions:

- **Scope**: how much is affected.
- **Severity**: how much harm it does.
- **Urgency**: how much time there is.
- **Tolerability**: whether it can be lived with.
- **Location** **(proposal)**: where the failure lies (in the task, the capability, the quality, the agreement or the intent).

Severity and urgency are independent of each other.

Possible responses: accept, accept with reservations, correct, escalate, or review the agreement or the intent.

**What is tolerable within the agreement is resolved at its own level; what is not gets escalated.** Tolerability marks the boundary of autonomy.

## 7. Slop

Something impeccable is beautiful; slop introduces ugliness. Images: a line that breaks the metre of a poem; a puzzle piece forced into a place it does not belong. Impeccable means zero slop.

### Figures

| Figure | Image | Slop in our work |
|---|---|---|
| **Form** | the line that breaks the metre | a term with two meanings; a section in the wrong language |
| **Fit** | the forced piece | a rule that contradicts another; something not traceable to the intent |
| **Economy** | the filler syllable | the same thing said twice; a sentence removable without loss |
| **Completeness** | the hole in the puzzle | a concept used but not defined; a task without verification |
| **Order** | stanzas out of place | something used before it is defined |
| **Sharpness** | the blurred piece | a sentence with two readings |
| **Truthfulness** | the trompe-l'oeil | claiming "verified" without evidence |

### Measurement (proposal)

An artefact A is structured: elements E with identifiers, a glossary G, declared patterns P, and declared relations `defines(e,t)`, `uses(e,t)`, `derives(e,x)`, `covers(e,c)`, `evidence(e)`, plus position `pos(e)`.

| Figure | Violations V |
|---|---|
| Form | #{(e,p) ∈ E×P : e breaks p} |
| Fit | #{e : no `derives` path to the intent} + #MUS(Σ) |
| Economy | \|Σ\| − \|minimum subset equivalent to Σ\| |
| Completeness | \|terms used \ terms defined\| |
| Order | #{(e,t) : uses(e,t) ∧ pos(e) < pos(defines(t))} |
| Sharpness | #{terms with >1 definition} + #{uses of words from a declared vague list} |
| Truthfulness | #{claims e : evidence(e) = ∅} |

Slop(A) = Σ V_f. A is impeccable iff Slop(A) = 0. No weights.

Contradiction and redundancy are made countable by writing elements as logical formulas Σ = {φₑ}: a contradiction is a minimal unsatisfiable subset (MUS); e is redundant iff Σ \ {φₑ} ⊨ φₑ. Judgement moves from verification to formalisation, where it is made once and recorded. The logic must be decidable (candidate: description logics).

### Tooling candidates (proposal, to be evaluated)

OWL 2 + reasoner (HermiT, Pellet, ELK); SHACL; SPARQL or Datalog; Z3 / MARCO for MUS; Alloy; Attempto Controlled English (APE, RACE); Vale. Temporal and graded aspects may need TLA+ or Alloy 6.

### Evaluation plan

Follow the pattern of karpathy/autoresearch:

1. A fixed evaluator the evaluated agent cannot modify: a corpus with deliberately seeded slop and known true counts per figure, plus a hidden hold-out corpus.
2. Metric: Σ_f |V_f detected − V_f true|; must be 0, and two runs must give the same number. Ties go to the simpler stack.
3. One editable implementation per candidate stack; keep/discard via git; results logged.
4. The loop is a delegated task with its own agreement: autonomous inside, validated by the user at the end.

## 8. Open questions

- Is quality a property of the result, or of the relationship between task and result?
- Does autonomy depend on verifiability, so that the more verifiable a result is, the more it can be delegated? **(proposal)**
- What are the dimensions of measurement, and how is product quality separated from process quality?
- When monitoring, how is intent drift told apart from legitimate evolution?
