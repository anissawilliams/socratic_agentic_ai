from datetime import datetime, timezone
from typing import Any

from langchain_core.messages import (
    messages_from_dict,
    messages_to_dict,
)

from app.graph.state import TutorCondition, TutorState
from app.models.evaluation import ResponseEvaluation
from app.models.routing import RouteDecision, RoutingRecord
from app.services.supabase import get_supabase_client
from app.socratic.phases import SocraticPhase


def serialize_state(state: TutorState) -> dict[str, Any]:
    """Convert TutorState into JSON-compatible data."""

    route_decision = state.get("route_decision")
    response_evaluation = state.get("response_evaluation")

    return {
        "session_id": state["session_id"],
        "participant_id": state["participant_id"],
        "messages": messages_to_dict(state["messages"]),
        "tutor_condition": (
            state["tutor_condition"].value
            if state.get("tutor_condition") is not None
            else None
        ),
        "current_turn_id": state.get("current_turn_id"),
        "current_phase": (
            state["current_phase"].value
            if state.get("current_phase") is not None
            else None
        ),
        "previous_phase": (
            state["previous_phase"].value
            if state.get("previous_phase") is not None
            else None
        ),
        "phase_history": [
            phase.value
            for phase in state.get("phase_history", [])
        ],
        "route_decision": (
            route_decision.model_dump(mode="json")
            if route_decision is not None
            else None
        ),
        "routing_history": [
            record.model_dump(mode="json")
            for record in state.get("routing_history", [])
        ],
        "response_evaluation": (
            response_evaluation.model_dump(mode="json")
            if response_evaluation is not None
            else None
        ),
        "pending_event": state.get("pending_event"),
        "last_student_message": state.get(
            "last_student_message",
            "",
        ),
        "is_complete": state.get("is_complete", False),
        "completed_at": state.get("completed_at"),
    }


def deserialize_state(data: dict[str, Any]) -> TutorState:
    """Rebuild TutorState from persisted JSON data."""

    tutor_condition = data.get("tutor_condition")
    current_phase = data.get("current_phase")
    previous_phase = data.get("previous_phase")
    route_decision = data.get("route_decision")
    response_evaluation = data.get("response_evaluation")

    return {
        "session_id": data["session_id"],
        "participant_id": data["participant_id"],
        "messages": messages_from_dict(
            data.get("messages", [])
        ),
        "tutor_condition": (
            TutorCondition(tutor_condition)
            if tutor_condition is not None
            else None
        ),
        "current_turn_id": data.get("current_turn_id"),
        "current_phase": (
            SocraticPhase(current_phase)
            if current_phase is not None
            else None
        ),
        "previous_phase": (
            SocraticPhase(previous_phase)
            if previous_phase is not None
            else None
        ),
        "phase_history": [
            SocraticPhase(phase)
            for phase in data.get("phase_history", [])
        ],
        "route_decision": (
            RouteDecision.model_validate(route_decision)
            if route_decision is not None
            else None
        ),
        "routing_history": [
            RoutingRecord.model_validate(record)
            for record in data.get("routing_history", [])
        ],
        "response_evaluation": (
            ResponseEvaluation.model_validate(
                response_evaluation
            )
            if response_evaluation is not None
            else None
        ),
        "pending_event": data.get("pending_event"),
        "last_student_message": data.get(
            "last_student_message",
            "",
        ),
        "is_complete": data.get("is_complete", False),
        "completed_at": data.get("completed_at"),
    }


def save_session(state: TutorState) -> None:
    """Persist the latest session snapshot."""

    client = get_supabase_client()

    payload = {
        "session_id": state["session_id"],
        "participant_id": state["participant_id"],
        "state": serialize_state(state),
        "is_complete": state["is_complete"],
        "updated_at": datetime.now(
            timezone.utc
        ).isoformat(),
    }

    client.table("tutor_sessions").upsert(
        payload,
        on_conflict="session_id",
    ).execute()


def load_session(session_id: str) -> TutorState | None:
    """Load a persisted session snapshot by session ID."""

    client = get_supabase_client()

    response = (
        client.table("tutor_sessions")
        .select("state")
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return deserialize_state(
        response.data[0]["state"]
    )