from app.graph.state import TutorState
from app.socratic.phases import SOCRATIC_PHASE_ORDER


def select_phase(state: TutorState) -> dict:
    """Select the next Socratic phase from the response evaluation."""

    current_phase = state["current_phase"]
    evaluation = state["response_evaluation"]

    if current_phase is None:
        raise ValueError(
            "Cannot select a phase without an active Socratic phase."
        )

    if evaluation is None:
        raise ValueError(
            "Cannot select a phase without a response evaluation."
        )

    if evaluation.decision == "stay":
        return {}

    current_index = SOCRATIC_PHASE_ORDER.index(current_phase)

    if current_index == len(SOCRATIC_PHASE_ORDER) - 1:
        return {
            "previous_phase": current_phase,
            "current_phase": None,
        }

    return {
        "previous_phase": current_phase,
        "current_phase": SOCRATIC_PHASE_ORDER[current_index + 1],
    }