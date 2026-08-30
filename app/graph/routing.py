from app.graph.state import TutorState


def route_after_phase_selection(state: TutorState) -> str:
    """Route based on whether a Socratic phase remains active."""
    if state["current_phase"] is None:
        return "generate_reflection"

    return "generate_response"