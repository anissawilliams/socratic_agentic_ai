"""Ask all four Socratic agents to respond to the identical conversation.

The sequential smoke test cannot tell you whether a phase is doing its own job,
because each phase sees a different transcript. Holding the input fixed makes
the agent the only variable: if four roles produce the same move from the same
input, the role prompts are not functioning as a manipulation.

Judge the output by reading it. An earlier version of this script scored
pairwise word overlap, which reported 0.06-0.24 on four responses that were
pedagogically interchangeable, so the number was worse than no number.

Run: .venv/bin/python -m scripts.compare_phases
Cost: one model call per agent per fixture.
"""

from uuid import uuid4

from langchain_core.messages import AIMessage, HumanMessage

from app.graph.state import TutorCondition, TutorState
from app.socratic.agents import (
    generate_aporia_response,
    generate_dialectic_response,
    generate_elenchus_response,
    generate_maieutics_response,
)
from app.socratic.context import phase_context, tag_phase
from app.socratic.phases import SOCRATIC_PHASE_ORDER, SocraticPhase

AGENTS = {
    SocraticPhase.ELENCHUS: generate_elenchus_response,
    SocraticPhase.APORIA: generate_aporia_response,
    SocraticPhase.MAIEUTICS: generate_maieutics_response,
    SocraticPhase.DIALECTIC: generate_dialectic_response,
}

OPENING = (
    "One of the main metrics that shows an academic paper is important and "
    "high-quality is the number of citations. What do you think — is that a "
    "fair claim?"
)


def tutor(content: str, phase: SocraticPhase | None = None) -> AIMessage:
    """A prior tutor turn, labelled with the role that produced it."""
    message = AIMessage(content=content)
    return message if phase is None else tag_phase(message, phase)


# Two points in a dialogue where different phases should behave differently.
# If the outputs do not diverge here, they will not diverge in a real session.
FIXTURES = {
    "confident learner, position stated and defended": [
        tutor(OPENING),
        HumanMessage(
            content=(
                "Yes, I think it's fair. If lots of researchers cite a paper, "
                "it means the paper was useful to them, and usefulness is a "
                "reasonable proxy for quality."
            )
        ),
        tutor(
            "You said usefulness is a reasonable proxy for quality. What "
            "makes you confident that the researchers citing a paper are "
            "endorsing it rather than disputing it?",
            SocraticPhase.ELENCHUS,
        ),
        HumanMessage(
            content=(
                "I suppose most citations are neutral or positive. People "
                "don't usually spend a whole paper arguing against something "
                "unimportant, so even a critical citation means it mattered."
            )
        ),
    ],
    "learner has conceded their account does not hold": [
        tutor(OPENING),
        HumanMessage(
            content=(
                "Citation count seems like a good measure of quality to me."
            )
        ),
        tutor(
            "You hold that citation count measures quality. Consider a paper "
            "that reported a striking result that later failed to replicate, "
            "and was cited hundreds of times by researchers pointing out the "
            "failure. Those two cannot both stand. Which do you give up?",
            SocraticPhase.APORIA,
        ),
        HumanMessage(
            content=(
                "Honestly that breaks what I said. That paper would score "
                "highly on citations and be low quality. So citation count "
                "can't be measuring quality directly. I'm not sure what it is "
                "measuring, though — attention, maybe? I don't know how I'd "
                "tell a good paper from a well-known one."
            )
        ),
    ],
}


def build_state(messages: list, phase: SocraticPhase) -> TutorState:
    return {
        "session_id": str(uuid4()),
        "participant_id": str(uuid4()),
        "messages": messages,
        "tutor_condition": TutorCondition.SOCRATIC,
        "current_phase": phase,
        "previous_phase": None,
        "pending_event": None,
        "phase_attempt_count": 0,
        "phase_turns_taken": 1,
        "current_turn_id": str(uuid4()),
        "last_student_message": messages[-1].content,
        "response_evaluation": {"hedging_detected": False},
        "next_action": None,
        "is_complete": False,
        "completed_at": None,
    }


for label, transcript in FIXTURES.items():
    print("=" * 78)
    print(label.upper())
    print("=" * 78)
    print(f"\nLearner's last message:\n  {transcript[-1].content}\n")
    print("Context every agent is given:")
    print(f"{phase_context(transcript)}\n")

    for phase in SOCRATIC_PHASE_ORDER:
        state = build_state(list(transcript), phase)
        print(f"--- {phase.value} ---")
        print(f"{AGENTS[phase](state).content}\n")
