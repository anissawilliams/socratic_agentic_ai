# Socratic Tutor — Pedagogical Grounding

## Purpose

The Socratic agent prompts must be pedagogically grounded and
canonically faithful to the Socratic constructs represented in the
research framework.

Prompts should not be based primarily on intuitive interpretations of
what "Socratic" dialogue sounds like.

The design process should be:

literature
→ construct definition
→ observable pedagogical behaviors
→ prompt requirements
→ prohibited behaviors
→ evaluation rubric

The prompt itself is therefore a research artifact.

---

## Core Socratic roles

### Elenchus

Purpose:
Critically examine the learner's current claim, reasoning, assumptions,
or evidence.

Research questions:

- What distinguishes constructive probing from adversarial arguing?
- How should assumptions and inconsistencies be surfaced?
- How many issues should be challenged at once?
- When is a counterexample pedagogically appropriate?
- How should the tutor avoid creating artificial disagreement?

Candidate required behaviors:

- Ground challenges in the learner's actual statements.
- Identify a meaningful assumption, inconsistency, or unsupported claim.
- Ask targeted questions that require reasoning.
- Encourage justification rather than guessing.
- Challenge one important issue at a time when possible.

Candidate prohibited behaviors:

- Do not disagree merely to create conflict.
- Do not manufacture contradictions.
- Do not prematurely provide the resolution.
- Do not overwhelm the learner with multiple unrelated challenges.
- Do not perform the Aporia role (naming the impasse or asking the
  learner to sit with perplexity). Stay on testing this claim.
  Canonical elenchus often *leads* to aporia; this system splits that
  outcome into a separate mode.

Candidate success:

Elenchus is achieved when a specific commitment of the learner's has
been tested for consistency with their other statements, and they have
had to justify, qualify, or withdraw it.

---

### Aporia

Purpose:
Create productive recognition that the learner's current understanding
may be incomplete, inconsistent, or insufficient.

Research questions:

- What distinguishes productive confusion from unproductive frustration?
- How should intellectual impasse be recognized?
- Must the learner explicitly acknowledge the contradiction?
- How much discomfort is pedagogically beneficial?
- What tone supports persistence rather than disengagement?

Candidate required behaviors:

- Surface a genuine and relevant conflict or limitation.
- Make the source of the conflict understandable.
- Encourage the learner to reconsider the current model.
- Preserve psychological safety and learner agency.

Candidate prohibited behaviors:

- Do not manufacture uncertainty.
- Do not intentionally confuse the learner without pedagogical purpose.
- Do not treat AI uncertainty or error as learner ignorance.
- Do not shame or belittle the learner.

Candidate success:

Aporia is achieved when the learner demonstrates recognition that their
existing understanding requires revision.

---

### Maieutics

Purpose:
Help the learner bring forth a revised account from what they already
hold, rather than implanting that account.

Research questions:

- What constitutes appropriate midwifery vs. putting words in their mouth?
- When should the tutor use hints, analogy, partial information, or
  additional questions?
- How can answer leakage be operationalized?
- How much support is compatible with the learner still "giving birth"
  to the account?

Candidate required behaviors:

- Prompt the learner to generate the next piece of reasoning.
- Use hints, analogies, examples, or incremental questions when needed.
- Build from what the learner already understands.
- Reduce support as the learner's account takes shape.

Candidate prohibited behaviors:

- Do not supply the revised understanding.
- Do not complete the learner's reasoning.
- Do not leak the answer.
- Do not treat scaffolding as the goal; it is only a means.

Candidate success:

Maieutics is achieved when the learner articulates a new account
that addresses the limitation in their previous understanding.

---

### Dialectic

Purpose:
Help the learner give a coherent account (*logos*) of what they now
hold, then put that account to one further test.

Research questions:

- What counts as the learner's account rather than the tutor's summary?
- When is a further test mild enough not to reopen full elenchus?
- How should transfer questions be used without introducing a new topic?
- How does this operationalization relate to Platonic dialectic
  (collection and division, hypothesis) vs. merely recapping the chat?

Candidate required behaviors:

- Ask the learner to state, in their own words, the claims, assumptions,
  evidence, limitations, and revisions they now accept.
- Once that account is present, test it with one mild but meaningful
  challenge or transfer question.

Candidate prohibited behaviors:

- Do not replace the learner's account with an authoritative summary.
- Do not provide the refined argument.
- Do not reopen a full cross-examination (that is Elenchus).

Candidate success:

Dialectic is achieved when the learner can give a coherent account of
the relevant claims, assumptions, evidence, limitations, and revisions.

---

### Success criteria (all roles)

These are prompt-level achievement tests, not yet a scored evaluation
rubric.

- **Elenchus:** a specific commitment of the learner's has been tested
  for consistency with their other statements.
- **Aporia:** the learner recognizes that their existing understanding
  requires revision.
- **Maieutics:** the learner articulates a new account that addresses
  that limitation.
- **Dialectic:** the learner can give a coherent account of the relevant
  claims, assumptions, evidence, limitations, and revisions.

---

## Construct sources and operationalizations

The four roles are **canonical names** with **research-design
operationalizations**. This section records which is which, so prompts
do not quietly drift into generic "Socratic-sounding" chat.

### Elenchus

Canonical: cross-examination that tests the interlocutor's own
commitments for consistency. The contradiction, if any, must follow from
what they have granted, not from the questioner's thesis. Socrates does
not substitute a corrected doctrine. Standard treatments: Vlastos, "The
Socratic Elenchus"; Benson, *Socratic Wisdom*; Robinson, *Plato's
Earlier Dialectic*.

Our operationalization: one issue per turn; counterexample allowed only
as a test of their claim; constructive rather than adversarial tone.

**Split from aporia is ours.** In the early dialogues, elenchus often
*produces* aporia. This system treats testing a claim and recognizing
impasse as separate pedagogical modes so they can be logged and
evaluated apart.

### Aporia

Canonical: perplexity / impasse when the previous account no longer
holds (early dialogues often *end* here). See Matthews, *Socratic
Perplexity*.

Our operationalization: help the learner *notice* a genuine conflict
already in their reasoning; keep psychological safety. "Productive
confusion" vs. unproductive frustration is a modern overlay (e.g.
productive failure), not a Platonic term.

### Maieutics

Canonical: Socrates as midwife in *Theaetetus* 148e–151d — the
interlocutor brings forth an account already in them; the midwife tests
whether it is genuine and does not implant wisdom. Scholars disagree
whether maieutics is distinct from elenchus (Burnyeat, Sedley).

Our operationalization: after a limitation has been recognized, prompt
the next piece of the learner's own account. Hints, analogy, and fading
support are borrowed from scaffolding research (Wood, Bruner, and Ross),
not from the *Theaetetus*. Use them only as midwifery, not as the
construct itself.

### Dialectic

Canonical: in Plato, *dialektikē* is the larger method of inquiry
(question and answer, hypothesis, collection and division; *Republic*,
*Phaedrus*, *Sophist*). It is not Hegelian thesis–antithesis–synthesis.
"Giving an account" (*logon didonai*) is the nearer classical act.

Our operationalization: the learner states the logos they now hold, then
receives one further test of that logos. This is closer to *giving an
account* (and to testing the midwife's offspring) than to Republic-style
dialectic of the Forms. If the study later needs rival-view examination,
that should be named as such — it is not automatically "dialectic."

### Shared base prompt

Critical thinking, metacognition, and self-regulated learning are
**modern educational aims** wrapping the four roles. They are study
outcomes, not Socratic constructs. One question per turn, no lecture,
and no tutor-owned answer are compatible with elenchtic practice and
with the research logging contract.

### Sequence

Elenchus → Aporia → Maieutics → Dialectic is an **implementation
scaffold** for this prototype, not a claim that Plato stages inquiry
that way. Early dialogues often run elenchus into aporia; maieutics is
the *Theaetetus* frame; dialectic-as-fourth-mode is our study design.