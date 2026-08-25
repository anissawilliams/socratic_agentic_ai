from datetime import datetime, timezone


def complete_session(state: dict) -> dict:
    """Runs only when the session has actually concluded. Today this just
    finalizes state cleanly; once persistence exists, this is where the
    full session record gets written (not per-turn — that's a different
    concern, this is the session-level summary)."""

    # TODO: once Firebase/Postgres exists, write the finalized session
    # record here (participant_id, full transcript, phase history, etc.)

    return {
        "is_complete": True,
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }