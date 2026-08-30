from app.graph.state import TutorState
from app.persistence.events import save_event

# SAVE TURN EVENTS TO SUPABASE - PER-TURN EVENTS

def _value(value):
    """Return enum value when present; otherwise return value unchanged."""
    return getattr(value, "value", value)


def log_turn(state: TutorState) -> dict:
    """Persist one completed Socratic tutoring turn."""

    last_message = state["messages"][-1]
    tutor_response = getattr(last_message, "content", str(last_message))

    save_event(
        session_id=state["session_id"],
        event_type="turn_completed",
        data={
            "current_phase": _value(state.get("current_phase")),
            "previous_phase": _value(state.get("previous_phase")),
            "phase_attempt_count": state["phase_attempt_count"],
            "response_evaluation": state["response_evaluation"],
            "student_message": state["last_student_message"],
            "tutor_response": tutor_response,
            "tutor_condition": _value(state.get("tutor_condition")),
        },
    )

    return {}