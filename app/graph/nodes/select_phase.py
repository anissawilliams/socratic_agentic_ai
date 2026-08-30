from app.graph.state import TutorState
from app.socratic.phases import SocraticPhase, SOCRATIC_PHASE_ORDER


MAX_ATTEMPTS_PER_PHASE = 3


def select_phase(state: TutorState) -> dict:
    """
    Selects the Socratic phase that should govern the next tutor response.

    A hedging response may keep the learner in the current phase until
    the maximum number of attempts is reached. Otherwise, the tutor
    advances to the next Socratic phase.

    When Dialectic is complete, current_phase becomes None so the graph
    can route into the reflection/exit workflow.
    """
    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError("Cannot select a phase when current_phase is None.")

    evaluation = state["response_evaluation"]
    hedging = evaluation["hedging_detected"]
    phase_attempt_count = state["phase_attempt_count"]

    should_stay = (
        hedging
        and phase_attempt_count < MAX_ATTEMPTS_PER_PHASE - 1
    )

    if should_stay:
        return {
            "phase_attempt_count": phase_attempt_count + 1,
        }

    current_index = SOCRATIC_PHASE_ORDER.index(current_phase)
    is_final_phase = current_index == len(SOCRATIC_PHASE_ORDER) - 1

    if is_final_phase:
        return {
            "previous_phase": current_phase,
            "current_phase": None,
            "phase_attempt_count": 0,
        }

    next_phase = SOCRATIC_PHASE_ORDER[current_index + 1]

    return {
        "previous_phase": current_phase,
        "current_phase": next_phase,
        "phase_attempt_count": 0,
    }