from app.graph.state import TutorState


def route_after_phase_selection(state: TutorState) -> str:
    """Route based on whether a Socratic phase remains active.

    When the phases are exhausted the session ends without a closing tutor
    message. The reflection stage is deliberately unwired: the scripted text
    asserted that the learner had revised their position, which is untrue of any
    participant who never held the opening premise. See "Reflection" in
    STUDY_DESIGN_QUESTIONS.md.
    """
    if state["current_phase"] is None:
        return "complete_session"

    return "generate_response"
