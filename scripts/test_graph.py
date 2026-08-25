# scripts/test_graph.py
from app.graph.graph import tutor_graph

initial_state = {
    "session_id": "test-session-1",
    "messages": [],
    "current_phase": "elenchus",
    "attempt_count": 0,
    "last_student_message": "maybe",
    "hedging_detected": False,
    "next_action": None,
    "is_complete": False,
    "completed_at": None,
}

result = tutor_graph.invoke(initial_state)

print("current_phase:", result["current_phase"])
print("attempt_count:", result["attempt_count"])
print("is_complete:", result["is_complete"])
print("last message:", result["messages"][-1])