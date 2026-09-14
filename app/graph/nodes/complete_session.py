from datetime import datetime, timezone

from langchain_core.messages import AIMessage


def complete_session(state: dict) -> dict:
    """Mark the session complete and provide a neutral sign-off."""
    return {
        "messages": [
            AIMessage(
                content=(
                    "Thank you for explaining your reasoning. "
                    "This discussion is now complete."
                )
            )
        ],
        "is_complete": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "pending_event": "session_completed",
    }