PHASE_ORDER = ["elenchus", "aporia", "maieutics", "dialectic", "reflection_exit"]
MAX_ATTEMPTS_PER_PHASE = 3


def decide_next_step(state: dict) -> dict:
    """Owns all 'what happens next' logic: stay-or-advance, which phase
    comes next, what the attempt count resets to, and whether the session
    is now complete. Phase-generation nodes downstream should never need
    to make any of these decisions themselves."""
    hedging = state.get("hedging_detected", False)
    current_phase = state["current_phase"]
    attempt_count = state["attempt_count"]

    should_stay = hedging and attempt_count < MAX_ATTEMPTS_PER_PHASE - 1

    if should_stay:
        next_phase = current_phase
        next_attempt = attempt_count + 1
    else:
        current_index = PHASE_ORDER.index(current_phase)
        is_last = current_index == len(PHASE_ORDER) - 1
        next_phase = current_phase if is_last else PHASE_ORDER[current_index + 1]
        next_attempt = 0

    return {
        "current_phase": next_phase,
        "attempt_count": next_attempt,
        "is_complete": next_phase == "reflection_exit",
    }