from dotenv import load_dotenv
load_dotenv()
from langchain_core.messages import AIMessage, HumanMessage

from app.content.scenarios import load_scenario
from app.graph.graph import tutor_graph
from app.graph.state import TutorCondition
from app.socratic.phases import SocraticPhase

from uuid import uuid4

OPENING = load_scenario().opening_question

CONSIDERED = (
    "Citation count can be useful because it shows that other researchers "
    "have engaged with the work."
)


def run_case(name: str, state: dict):
    print(f"\n--- {name} ---")
    result = tutor_graph.invoke(state)

    print("current_phase:", result["current_phase"])
    print("previous_phase:", result["previous_phase"])
    print("phase_attempt_count:", result["phase_attempt_count"])
    print("phase_turns_taken:", result["phase_turns_taken"])
    print("response_evaluation:", result["response_evaluation"])
    print("is_complete:", result["is_complete"])
    print("completed_at:", result["completed_at"])
    print("last message:", result["messages"][-1])

    return result


base_state = {
    "session_id": str(uuid4()),
    "participant_id": str(uuid4()),
    "messages": [],
    "tutor_condition": TutorCondition.SOCRATIC,
    "previous_phase": None,
    "response_evaluation": {
        "hedging_detected": False,
    },
    "is_complete": False,
    "completed_at": None,
}


def student_turn(phase, turns_taken, answer, **overrides):
    """One student message arriving mid-session."""
    return {
        **base_state,
        "session_id": str(uuid4()),
        "current_phase": phase,
        "phase_attempt_count": 0,
        "phase_turns_taken": turns_taken,
        "last_student_message": answer,
        "messages": [
            AIMessage(content=OPENING),
            HumanMessage(content=answer),
        ],
        **overrides,
    }


# 1. The learner's first answer is cross-examined by Elenchus itself.
#    Elenchus has not spoken yet (phase_turns_taken=0), so a considered
#    answer must not skip it.
run_case(
    "first answer is cross-examined by elenchus",
    student_turn(SocraticPhase.ELENCHUS, 0, CONSIDERED),
)


# 2. Hedging after Elenchus has spoken keeps the learner in Elenchus.
run_case(
    "hedging stays in elenchus",
    student_turn(SocraticPhase.ELENCHUS, 1, "maybe"),
)


# 3. A considered answer after Elenchus has spoken advances to Aporia.
run_case(
    "elenchus advances to aporia",
    student_turn(SocraticPhase.ELENCHUS, 1, CONSIDERED),
)


# 4. Dialectic complete → reflection → session complete.
run_case(
    "dialectic exits to reflection",
    student_turn(
        SocraticPhase.DIALECTIC,
        1,
        "I would also look at the methodology, evidence, replication, "
        "and how the conclusions are supported.",
        previous_phase=SocraticPhase.MAIEUTICS,
    ),
)
