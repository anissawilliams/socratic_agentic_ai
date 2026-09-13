from app.graph.next_move import choose_next_move
from app.graph.state import TutorState


def choose_next_move_node(state: TutorState) -> dict:
    """Select the role and target for the next tutor response."""

    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError(
            "Cannot choose a move without an active Socratic phase."
        )

    route_decision = choose_next_move(
        messages=state["messages"],
        current_phase=current_phase,
        phase_history=state["phase_history"],
        routing_history=state["routing_history"],
        last_student_message=state["last_student_message"],
    )

    return {
        "route_decision": route_decision,
    }