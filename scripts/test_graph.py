from app.graph.graph import tutor_graph
from app.graph.state import TutorCondition
from app.socratic.phases import SocraticPhase
from uuid import uuid4

def run_case(name: str, state: dict):
    print(f"\n--- {name} ---")
    result = tutor_graph.invoke(state)

    print("current_phase:", result["current_phase"])
    print("previous_phase:", result["previous_phase"])
    print("phase_attempt_count:", result["phase_attempt_count"])
    print("response_evaluation:", result["response_evaluation"])
    print("is_complete:", result["is_complete"])
    print("completed_at:", result["completed_at"])
    print("last message:", result["messages"][-1])

    return result


base_state = {
    "session_id": str(uuid4()),
    "messages": [],
    "tutor_condition": TutorCondition.SOCRATIC,
    "previous_phase": None,
    "response_evaluation": {
        "hedging_detected": False,
    },
    "is_complete": False,
    "completed_at": None,
}


# 1. Hedging → stay in Elenchus
run_case(
    "hedging stays in elenchus",
    {
        **base_state,
        "session_id": str(uuid4()),
        "current_phase": SocraticPhase.ELENCHUS,
        "phase_attempt_count": 0,
        "last_student_message": "maybe",
    },
)


# 2. Confident response → advance Elenchus → Aporia
run_case(
    "elenchus advances to aporia",
    {
        **base_state,
        "session_id": str(uuid4()),
        "current_phase": SocraticPhase.ELENCHUS,
        "phase_attempt_count": 0,
        "last_student_message":
            "Citation count can be useful because it shows that other researchers have engaged with the work.",
    },
)


# 3. Dialectic complete → reflection → session complete
run_case(
    "dialectic exits to reflection",
    {
        **base_state,
        "session_id": str(uuid4()),
        "current_phase": SocraticPhase.DIALECTIC,
        "previous_phase": SocraticPhase.MAIEUTICS,
        "phase_attempt_count": 0,
        "last_student_message":
            "I would also look at the methodology, evidence, replication, and how the conclusions are supported.",
    },
)