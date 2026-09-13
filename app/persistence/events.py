import json
import logging
import os
import tempfile
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from app.services.supabase import get_supabase_client


logger = logging.getLogger(__name__)

EventType = Literal[
    "turn_completed",
    "reflection_generated",
    "session_completed",
]

OUTBOX_DIR = (
    Path(__file__).resolve().parents[2]
    / ".local"
    / "tutor_event_outbox"
)


def _deliver_event(path: Path) -> bool:
    """Remove the local copy only after Supabase acknowledges delivery."""
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))

        client = get_supabase_client()

        client.table("tutor_events").upsert(
            payload,
            on_conflict="delivery_id",
            ignore_duplicates=True,
            returning="minimal",
        ).execute()

        path.unlink(missing_ok=True)
        return True

    except Exception:
        logger.exception(
            "Event delivery failed; retained locally for retry: %s",
            path.name,
        )
        return False


def save_event(
    session_id: str,
    event_type: EventType,
    data: dict[str, Any],
) -> None:
    delivery_id = str(uuid4())

    payload = {
        "delivery_id": delivery_id,
        "session_id": session_id,
        "event_type": event_type,
        "data": data,
    }

    OUTBOX_DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    path = OUTBOX_DIR / f"{delivery_id}.json"

    # Finish writing before making the file available for delivery.
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=OUTBOX_DIR,
        suffix=".tmp",
        delete=False,
    ) as temporary:
        temporary_path = Path(temporary.name)

        try:
            json.dump(payload, temporary, ensure_ascii=False)
            temporary.flush()
            os.fsync(temporary.fileno())
        except Exception:
            temporary_path.unlink(missing_ok=True)
            raise

    temporary_path.replace(path)

    # A remote failure is logged, but the local event is preserved.
    _deliver_event(path)


def flush_pending_events() -> dict[str, int]:
    """Retry queued events, stopping if delivery fails."""
    delivered = 0

    for path in sorted(OUTBOX_DIR.glob("*.json")):
        if not _deliver_event(path):
            break

        delivered += 1

    return {
        "delivered": delivered,
        "pending": len(list(OUTBOX_DIR.glob("*.json"))),
    }