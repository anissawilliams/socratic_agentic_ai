import uuid

from app.persistence.events import save_event


session_id = str(uuid.uuid4())

save_event(
    session_id=session_id,
    event_type="test",
    data={
        "message": "Supabase logging works",
        "source": "test_supabase.py",
    },
)

print("Event written successfully:", session_id)