from datetime import datetime, timezone


def complete_session(state: dict) -> dict:
    """
    Finalize a tutoring session after the reflection/exit workflow.

    Session-level persistence can be added here later. Per-turn/event
    logging remains a separate concern.
    """

    return {
        "is_complete": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }