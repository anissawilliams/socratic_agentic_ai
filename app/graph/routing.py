from app.graph.state import TutorState


def route_after_evaluation(state: TutorState) -> str:
    """Route to session completion or the next Socratic move."""

    evaluation = state.get("response_evaluation")

    if evaluation is None:
        raise ValueError(
            "Cannot route after evaluation without a response evaluation."
        )

    if evaluation.session_goal_satisfied:
        return "complete_session"

    return "choose_next_move"
