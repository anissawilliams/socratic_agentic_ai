from typing import Any

from app.graph.state import TutorState
from app.persistence.events import save_event


def _enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def build_event_data(state: TutorState) -> dict:
    """Build the JSONB payload for the event currently pending."""
    event_type = state["pending_event"]

    base_data = {
        "current_phase": _enum_value(state.get("current_phase")),
        "previous_phase": _enum_value(state.get("previous_phase")),
        "phase_attempt_count": state.get("phase_attempt_count"),
        "tutor_condition": _enum_value(state.get("tutor_condition")),
    }

    if event_type == "turn_completed":
        last_message = state["messages"][-1]

        return {
            **base_data,
            "student_message": state["last_student_message"],
            "tutor_response": getattr(
                last_message,
                "content",
                str(last_message),
            ),
            "response_evaluation": state["response_evaluation"],
        }

    if event_type == "reflection_generated":
        last_message = state["messages"][-1]

        return {
            **base_data,
            "reflection": getattr(
                last_message,
                "content",
                str(last_message),
            ),
        }

    if event_type == "session_completed":
        return {
            **base_data,
            "completed_at": state["completed_at"],
        }

    raise ValueError(f"Unsupported event type: {event_type}")


def log_event(state: TutorState) -> dict:
    event_type = state.get("pending_event")

    #print("LOG_EVENT:", event_type, state["session_id"])

    if event_type is None:
        return {}

    #print("BUILDING EVENT DATA:", build_event_data(state))
    save_event(
        session_id=state["session_id"],
        event_type=event_type,
        data=build_event_data(state),
    )

    return {
        "pending_event": None,
    }