from typing import Any

from app.graph.state import TutorState
from app.persistence.events import save_event


TURN_EVENT_SCHEMA_VERSION = "turn_completed.v3"
SESSION_EVENT_SCHEMA_VERSION = "session_completed.v1"


def _enum_value(value: Any) -> Any:
    """Return an enum's stored value, or the original value."""
    return getattr(value, "value", value)


def _phase_history(state: TutorState) -> list[str]:
    return [
        _enum_value(phase)
        for phase in state.get("phase_history", [])
    ]


def build_event_data(state: TutorState) -> dict:
    """Build the JSONB payload for the event currently pending."""

    event_type = state["pending_event"]
    route_decision = state.get("route_decision")
    current_phase = state.get("current_phase")
    evaluation = state.get("response_evaluation")

    base_data = {
        "participant_id": state["participant_id"],
        "turn_id": state.get("current_turn_id"),
        "tutor_condition": _enum_value(
            state.get("tutor_condition")
        ),
        "current_phase": _enum_value(current_phase),
        "previous_phase": _enum_value(
            state.get("previous_phase")
        ),
        "phase_history": _phase_history(state),
    }

    if event_type == "turn_completed":
        if route_decision is None:
            raise ValueError(
                "Cannot log a completed turn without a routing decision."
            )

        last_message = state["messages"][-1]

        if route_decision.action == "stay":
            phase_before_move = current_phase
        else:
            phase_before_move = state.get("previous_phase")

        return {
            **base_data,
            "event_schema_version": TURN_EVENT_SCHEMA_VERSION,
            "student_message": state["last_student_message"],
            "tutor_response": getattr(
                last_message,
                "content",
                str(last_message),
            ),
            "phase_before_move": _enum_value(
                phase_before_move
            ),
            "selected_phase": _enum_value(
                route_decision.next_phase
            ),
            "transition_action": route_decision.action,
            "routing_topic": route_decision.topic,
            "routing_move_type": route_decision.move_type,
            "routing_target": route_decision.target,
            "routing_reasoning_summary": (
                route_decision.reasoning_summary
            ),
            "routing_avoid_repeating": (
                route_decision.avoid_repeating
            ),
            "route_decision": route_decision.model_dump(
                mode="json"
            ),
            "response_evaluation": (
                evaluation.model_dump(mode="json")
                if evaluation is not None
                else None
            ),
            "routing_history": [
                record.model_dump(mode="json")
                for record in state["routing_history"]
            ],
        }

    if event_type == "session_completed":
        last_message = state["messages"][-1]

        return {
            **base_data,
            "event_schema_version": (
                SESSION_EVENT_SCHEMA_VERSION
            ),
            "student_message": state["last_student_message"],
            "tutor_response": getattr(
                last_message,
                "content",
                str(last_message),
            ),
            "response_evaluation": (
                evaluation.model_dump(mode="json")
                if evaluation is not None
                else None
            ),
            "completed_at": state.get("completed_at"),
            "routing_history": [
                record.model_dump(mode="json")
                for record in state["routing_history"]
            ],
        }

    raise ValueError(
        f"Unsupported event type: {event_type}"
    )


def log_event(state: TutorState) -> dict:
    """Persist the state's pending research event."""

    event_type = state.get("pending_event")

    if event_type is None:
        return {}

    save_event(
        session_id=state["session_id"],
        event_type=event_type,
        data=build_event_data(state),
    )

    return {
        "pending_event": None,
    }