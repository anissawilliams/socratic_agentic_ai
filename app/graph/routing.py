from app.graph.state import TutorState


def route_after_phase_selection(state: TutorState) -> str:
    """Route to response generation or session completion."""

    if state["current_phase"] is None:
        return "complete_session"

    return "generate_response"
