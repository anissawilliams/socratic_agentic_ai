from app.graph.state import TutorState
from app.models.routing import RoutingRecord


def select_phase(state: TutorState) -> dict:
    """Validate and apply the router's proposed decision."""

    current_phase = state["current_phase"]
    route_decision = state["route_decision"]

    if current_phase is None:
        raise ValueError(
            "Cannot select a phase without an active phase."
        )

    if route_decision is None:
        raise ValueError(
            "Cannot select a phase without a routing decision."
        )

    next_phase = route_decision.next_phase
    phase_history = state["phase_history"]

    if next_phase == current_phase:
        expected_action = "stay"
    elif next_phase in phase_history:
        expected_action = "revisit"
    else:
        expected_action = "switch"

    corrected_decision = route_decision.model_copy(
        update={
            "action": expected_action,
        }
    )

    routing_record = RoutingRecord(
        phase=next_phase,
        topic=corrected_decision.topic,
        move_type=corrected_decision.move_type,
        target=corrected_decision.target,
    )

    updates: dict = {
        "route_decision": corrected_decision,
        "routing_history": [
            *state["routing_history"],
            routing_record,
        ],
    }

    if next_phase != current_phase:
        updates.update(
            {
                "previous_phase": current_phase,
                "current_phase": next_phase,
                "phase_history": [
                    *phase_history,
                    next_phase,
                ],
            }
        )

    return updates