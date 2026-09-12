# Study design questions

Open decisions that the implementation cannot settle on its own, with the
evidence from the prototype that raised them. Written for readers who have not
been in the code.

Each item states what is at stake, what we observed, and the options. Where an
engineering recommendation exists it is labelled as such — the research calls
are the team's.

---

## Background: what the prototype does today

A participant is shown a fixed opening question (whether citation count
indicates a paper's quality). Their reply is evaluated by a heuristic, a router
selects a Socratic phase, an agent for that phase generates the tutor's
response, and the turn is logged. Phases advance through a fixed order:

    elenchus → aporia → maieutics → dialectic → reflection

Each phase is a system prompt given to the same model
(`gpt-4o-mini-2024-07-18`). Phases are not separate graph nodes; the router
picks which role speaks next.

---

## 1. Should a phase speak when its precondition is not met?

**At stake:** whether "Socratic phase" is a real manipulation.

**What we observed.** We built a harness that gives all four phase agents the
*same* conversation, so the phase is the only variable
(`scripts/compare_phases.py`). Initially all four produced the same
pedagogical move — with a confident learner every phase cross-examined, and
with a learner who had just conceded, every phase asked some version of "what
other criteria would you use?" The phase label was decorative.

After rewriting each role to make a mechanically distinct move and telling each
agent which moves earlier phases had already made, three of the four separate
cleanly. The exception is instructive: **a phase drifts into a neighbouring
role when its own precondition does not hold.** Asked to speak to a learner who
had *already* reached impasse, the aporia agent had nothing to do and began
asking for criteria, which is maieutics' job. Asked to speak before anything
had been conceded, maieutics and dialectic complied rather than declining.

The agents never fail — they always produce a plausible question. That is why
this stayed invisible, and it would have stayed invisible in the logs too,
since the logs would faithfully record `phase = aporia` beside text doing
maieutics.

**Options**

1. Keep the fixed sequence. Simple, but accept that phase fidelity will be
   imperfect and must be measured rather than assumed.
2. Gate each phase on a precondition the router checks (e.g. maieutics only
   after the learner concedes a limitation). Phases may then be skipped, so
   participants receive different sequences.
3. Let a phase decline to speak and hand control back to the router.

Options 2 and 3 mean participants no longer all receive the same phase
sequence, which changes what the conditions are comparing.

---

## 2. Is aporia a tutor move or a learner state?

**At stake:** whether there are four tutor roles or three.

In Plato, aporia is not something Socrates *does* — it is the state the
interlocutor is left in by elenchus. Our prompts already half-admit this: the
elenchus prompt has to explicitly forbid "switch into Aporia," and the aporia
prompt insists the impasse "must already be in their reasoning."

We are asking a model to perform a speech act that in the source material is an
effect rather than a move, and aporia is the role that drifts most.

**Options**

1. Keep four tutor roles, with aporia defined as *holding* the learner at an
   impasse they have reached (its current definition).
2. Treat aporia as a learner state the router detects, leaving three tutor
   roles: elenchus, maieutics, dialectic. Aporia becomes a measured outcome —
   arguably a better dependent variable than a phase label.

This is a construct-validity question, not an implementation preference.

---

## 3. Turn counts differ across conditions (dose confound)

**At stake:** whether a condition difference is attributable to Socratic
questioning or to time on task.

An engaged participant currently completes the questioning sequence in roughly
five tutor turns, because each phase advances as soon as it has spoken once. A
direct-answer control that runs to a 12-turn cap would give those participants
substantially more interaction. Any difference in outcomes would then be
confounded with dose.

**Needed:** a stopping rule that equates exposure across conditions — matched
turn counts, matched time, or matched task completion. `MIN_TURNS_PER_PHASE`
in `app/graph/nodes/select_phase.py` is the lever on the questioning side.

---

## 4. What ends a session?

Currently a session ends when the phase sequence completes. Alternatives are a
turn cap, a time limit, or participant choice. This interacts with item 3, and
it determines what "abandonment" means for analysis — a participant who stops
replying at turn 3 needs to be distinguishable from one who finished.

---

## 5. Blinding

**At stake:** whether participants can see their experimental assignment.

`GET /auth/me` returns the participant's `condition` to the browser, and the
tutor response returns `current_phase`. Both are visible in browser developer
tools. A participant who inspects them learns which arm they are in and sees
the phase labels as the tutor moves through them.

**Engineering recommendation:** stop sending both to the client unless the
frontend genuinely needs them. The phase indicator in the UI is the thing to
check — if participants are shown phase names deliberately, that is a design
choice to make explicitly rather than by accident.

---

## 6. Condition names are not settled

The code currently defines `socratic`, `scaffolded`, and `direct_chat`. A
separate implementation draft proposed a different set. The set has already
changed once.

Two consequences: renaming breaks continuity with data already logged under the
old names, and any database constraint on the old values will reject the new
ones. Whatever the final set is, it should be fixed before data collection and
the codes should be treated as permanent identifiers, not labels.

---

## 7. Routing is driven by a heuristic, not a measure

The router currently decides whether a participant is hedging from response
length and a list of hedge phrases. Everything downstream — which phase speaks,
how long they stay in it — follows from that heuristic.

Two implications. It is a **research instrument** and needs validating against
human coding of the same responses before conclusions rest on it. And a richer
`ResponseEvaluation` model exists in the code but is unpopulated, so the
intended structured evaluation is not yet driving anything.

The prototype stores the heuristic's *inputs* alongside its verdict so this
validation is possible after the fact.

---

## 8. LLM-as-judge outcomes need human validation

Planned evaluators (Socratic role fidelity, routing appropriateness,
direct-answer leakage, trajectory coherence) would be scored by a model. Any of
these used as a research outcome needs agreement with a human-coded subset
reported before the scores are trusted. Item 1 makes role fidelity the most
urgent of these.

---

## 9. Model provenance

The model is now pinned to `gpt-4o-mini-2024-07-18`. Before this, the code used
the floating `gpt-4o-mini` alias, which points at different snapshots over
time.

**Consequence:** turns logged before the pin are attributable only to "whatever
mini was that day" and should be treated as pilot data, not study data. The
model must stay fixed for the duration of collection, since the tutor's
behavior is the manipulation.

Separately: the phase-collapse described in item 1 was observed on mini. A
larger model may separate the roles more readily. Worth a comparison run before
concluding how much is prompt design and how much is model capacity.

---

## 10. Pedagogical constraints in the shared prompt

Two constraints apply to every role and are worth explicit team review, since
they shape every tutor utterance:

**Affirmation is now forbidden.** Every response previously opened with praise
("That's an insightful distinction"). This is now banned on the grounds that
affirmation trains the learner to seek the tutor's approval, which works
against the study's aim. Psychological safety is preserved by not belittling
the learner rather than by flattering them. If the team wants rapport-building
affirmation for engagement or retention reasons, that trade-off should be made
deliberately.

**Scope is constrained to one line of inquiry per response** rather than a hard
one-question limit, so the tutor may restate or sharpen a question but may not
open a second topic or offer a menu of directions. The aim is to keep the
participant from going astray.

---

## 11. Content and instruments

The opening question is currently hard-coded, and there is one scenario. Open
questions: how many scenarios, whether they are assigned by course, and where
scenario and instrument text lives so that analysis years later can reconstruct
exactly what a participant saw.

The reflection/exit stage still uses scripted text with no agent behind it.

---

## 12. Privacy and retention

- Whether prompts, participant text, and tutor responses are retained in
  LangSmith during collection, and under what retention settings.
- Whether participant free text may leave the primary datastore at all.
- Consent, withdrawal, and data-deletion requirements, and what they imply for
  append-only records.

---

## Already decided

| Decision | Resolution |
| --- | --- |
| Repeat participation | A participant may have several sessions; only one open at a time |
| Condition assignment | Stored once on the participant record; does not change |
| Model | Pinned to a dated snapshot for the duration of collection |
| Affirmation in tutor responses | Not permitted |
| Response scope | One line of inquiry per response |
| Authentication | Tutor endpoints require an enrolled participant; sessions are owned |
