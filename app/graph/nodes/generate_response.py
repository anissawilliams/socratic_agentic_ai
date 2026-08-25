from app.prompts.socratic import PHASE_CONTENT, PHASE_ORDER


def generate_response(state: dict) -> dict:
    """Resolves next_action ('stay'/'advance') into the actual next
    phase + attempt_count, and picks the content line. Deterministic for
    now — this is the node that becomes LLM-driven later; the surrounding
    graph shouldn't need to change when it does."""

    current_phase = state["current_phase"]
    action = state["next_action"]

    if action == "stay":
        next_phase = current_phase
        next_attempt = state["attempt_count"] + 1
    else:
        current_index = PHASE_ORDER.index(current_phase)
        is_last = current_index == len(PHASE_ORDER) - 1
        next_phase = current_phase if is_last else PHASE_ORDER[current_index + 1]
        next_attempt = 0

    lines = PHASE_CONTENT[next_phase]
    line = lines[min(next_attempt, len(lines) - 1)]

    return {
        "current_phase": next_phase,
        "attempt_count": next_attempt,
        "messages": [{"role": "assistant", "content": line}],
        "is_complete": next_phase == "reflection_exit",
    }