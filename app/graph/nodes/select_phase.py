from app.graph.state import TutorState


def select_phase(state: TutorState) -> dict:
    """Apply the router's selected Socratic phase to the tutor state."""

    current_phase = state["current_phase"]
    route_decision = state["route_decision"]

    if current_phase is None:
        raise ValueError(
            "Cannot select a phase without an active Socratic phase."
        )

    if route_decision is None:
        raise ValueError(
            "Cannot select a phase without a route decision."
        )

    next_phase = route_decision.next_phase
    phase_history = state["phase_history"]

    if next_phase == current_phase:
        expected_action = "stay"
    elif next_phase in phase_history:
        expected_action = "revisit"
    else:
        expected_action = "switch"

    updates: dict = {
        # Do not trust the model to label the transition correctly.
        # The application derives it deterministically.
        "route_decision": route_decision.model_copy(
            update={"action": expected_action}
        ),
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