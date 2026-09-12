from app.graph.state import TutorState
from app.socratic.phases import SocraticPhase, SOCRATIC_PHASE_ORDER


MAX_ATTEMPTS_PER_PHASE = 3

# A phase must generate at least this many tutor turns before the router may
# advance past it. The scripted opening question does not count: elenchus can
# only cross-examine a position the learner has already stated.
MIN_TURNS_PER_PHASE = 1


def select_phase(state: TutorState) -> dict:
    """
    Selects the Socratic phase that will generate the next tutor response.

    `current_phase` names the phase that speaks next, never the one that just
    spoke, so the router cannot advance past a phase before that phase has
    generated a turn.

    Once the phase has spoken, a hedging response may keep the learner in it
    until the maximum number of attempts is reached. Otherwise the tutor
    advances through SOCRATIC_PHASE_ORDER.

    When Dialectic is complete, current_phase becomes None so the graph
    can route to complete_session (no closing tutor turn).
    """
    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError("Cannot select a phase when current_phase is None.")

    evaluation = state["response_evaluation"]
    hedging = evaluation["hedging_detected"]
    phase_attempt_count = state["phase_attempt_count"]
    phase_turns_taken = state.get("phase_turns_taken", 0)

    # The learner is responding to the opening question or to the previous
    # phase. This phase has not done its own work yet, so there is nothing
    # about it to evaluate.
    if phase_turns_taken < MIN_TURNS_PER_PHASE:
        return {}

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
            "phase_turns_taken": 0,
        }

    next_phase = SOCRATIC_PHASE_ORDER[current_index + 1]

    return {
        "previous_phase": current_phase,
        "current_phase": next_phase,
        "phase_attempt_count": 0,
        "phase_turns_taken": 0,
    }
