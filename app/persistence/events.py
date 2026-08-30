from typing import Any, Literal
from app.services.supabase import get_supabase_client


EventType = Literal[
    "turn_completed",
    "reflection_generated",
    "session_completed",
]




# SAVE EVENTS TO SUPABASE 
def save_event(
    session_id: str,
    event_type: EventType,
    data: dict[str, Any],
) -> None:
    client = get_supabase_client()

    client.table("tutor_events").insert(
        {
            "session_id": session_id,
            "event_type": event_type,
            "data": data,
        }
    ).execute()