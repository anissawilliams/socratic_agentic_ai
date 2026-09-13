from app.graph.next_move import choose_next_move
from app.graph.state import TutorState


def choose_next_move_node(state: TutorState) -> dict:
    """Choose the pedagogical role for the tutor's next response."""

    current_phase = state["current_phase"]
    evaluation = state["response_evaluation"]

    if current_phase is None:
        raise ValueError(
            "Cannot choose the next move without an active Socratic phase."
        )

    if evaluation is None:
        raise ValueError(
            "Cannot choose the next move without a response evaluation."
        )

    route_decision = choose_next_move(
        messages=state["messages"],
        current_phase=current_phase,
        phase_history=state["phase_history"],
        evaluation=evaluation,
    )

    return {
        "route_decision": route_decision,
    }