PHASE_ORDER = ["elenchus", "aporia", "maieutics", "dialectic", "reflection_exit"]
MAX_ATTEMPTS_PER_PHASE = 3

# This is a rule-based stand-in for the eventual Triage agent — same interface, will be replaced by an LLM-backed decision-making node

def decide_next_step(state: dict) -> dict:
    """Pure decision: 'stay' or 'advance'. Does not resolve what phase
    comes next — that's a separate concern, resolved in generate_response."""
    hedging = state.get("hedging_detected", False)
    attempt_count = state["attempt_count"]

    if hedging and attempt_count < MAX_ATTEMPTS_PER_PHASE - 1:
        decision = "stay"
    else:
        decision = "advance"

    return {"next_action": decision}