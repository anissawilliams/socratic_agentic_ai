from app.graph.state import TutorState


def log_event(state: TutorState) -> dict:
    """Finalize graph state before the API records the typed transaction."""
    return {"pending_event": None}
