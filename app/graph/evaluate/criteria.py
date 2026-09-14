from app.socratic.phases import SocraticPhase


# These criteria describe whether a pedagogical move has accomplished
# its immediate purpose. Satisfying a criterion does not automatically
# require changing phases or ending the discussion.

PHASE_EVALUATION_CRITERIA: dict[SocraticPhase, str] = {
    SocraticPhase.ELENCHUS: """
The immediate Elenchus goal is satisfied when the learner has explained
a reason, assumption, or source of evidence supporting one specific
claim.

The learner does not need to prove the claim, change position, or
exhaust every possible justification.

A productive Elenchus follow-up may still remain when:
- a newly supplied reason contains an assumption worth examining;
- the relationship between the evidence and claim is unclear;
- the learner introduces a new supporting claim;
- the learner applies the reason without explaining the standard being used.

Do not mark the goal unsatisfied merely because the learner disagrees
with the tutor or gives a qualified answer.
""",

    SocraticPhase.APORIA: """
The immediate Aporia goal is satisfied when the learner has examined a
genuine difficulty grounded in the dialogue and has clarified what
remains unresolved or why the apparent difficulty does not hold.

A genuine difficulty may be:
- two learner commitments that appear incompatible in the same context;
- a relevant case the learner's account does not yet explain;
- an uncertainty or limitation the learner has acknowledged.

The learner does not need to abandon a claim, admit defeat, or revise a
coherent position.

Do not mark the goal satisfied based on a conflict introduced only by
the tutor. If the learner resolves or rejects an apparent conflict with
a coherent clarification, recognize that response as addressing the
Aporia move.
""",

    SocraticPhase.MAIEUTICS: """
The immediate Maieutics goal is satisfied when the learner contributes
a concrete element that develops their account.

A concrete contribution may include:
- a criterion;
- a distinction;
- an example;
- a relationship between ideas;
- a possible explanation;
- a proposed standard;
- a qualification of an earlier claim.

A productive Maieutics follow-up may remain when the new element needs
to be made more precise, connected to the learner's claim, or applied
to the case under discussion.

Do not require the learner to accept an idea supplied by the tutor.
The developing account must remain the learner's own.
""",

    SocraticPhase.DIALECTIC: """
The immediate Dialectic goal is satisfied when the learner has compared,
applied, tested, or integrated parts of their account in response to a
specific question.

This may include:
- applying the account to a relevant case;
- comparing competing considerations;
- explaining how multiple criteria work together;
- identifying the limits of the account;
- integrating earlier reasoning into a more precise position.

Satisfying the Dialectic goal does not mean the session is complete.
Further discussion may examine new claims, evidence, implications, or
applications that emerge from the learner's response.

Do not evaluate overall session completion here.
""",
}