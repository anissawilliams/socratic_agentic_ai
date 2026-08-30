# temporary assessment node - will be replaced with LLM-driven assessment
HEDGE_WORDS = ["maybe", "i guess", "i don't know", "not sure", "i think so"]


def looks_like_hedging(answer: str) -> bool:
    lower = answer.lower()
    too_short = len(answer.strip().split()) < 5
    has_hedge = any(w in lower for w in HEDGE_WORDS)
    return too_short or has_hedge


def assess_response(state: dict) -> dict:
    """Deterministic assessment for now — mirrors the frontend exactly.
    Returns only what changes; LangGraph merges this into state."""
    hedging = looks_like_hedging(state["last_student_message"])
    return {"hedging_detected": hedging}  