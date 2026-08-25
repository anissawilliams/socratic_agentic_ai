from fastapi import APIRouter
from pydantic import BaseModel

from app.graph.graph import tutor_graph
from app.prompts.socratic import PHASE_CONTENT
router = APIRouter()

# In-memory session store for now — no persistence yet, matches today's
# "no logging, just testing agentic pieces" scope. Sessions vanish on
# server restart; that's fine until Firebase lands.
_sessions: dict[str, dict] = {}


class TutorMessageRequest(BaseModel):
    session_id: str
    message: str


class TutorMessageResponse(BaseModel):
    message: str
    current_phase: str
    attempt_count: int
    is_complete: bool


def _new_session_state(session_id: str) -> dict:
    return {
        "session_id": session_id,
        "messages": [],
        "current_phase": "elenchus",
        "attempt_count": 0,
        "last_student_message": "",
        "hedging_detected": False,
        "next_action": None,
        "is_complete": False,
        "completed_at": None,
    }


@router.post("/tutor/message", response_model=TutorMessageResponse)
async def send_message(req: TutorMessageRequest):
    state = _sessions.get(req.session_id) or _new_session_state(req.session_id)
    state["last_student_message"] = req.message
    state["last_student_message"] = req.message
    state["messages"] = state.get("messages", []) + [{"role": "user", "content": req.message}]

    result = tutor_graph.invoke(state)
    _sessions[req.session_id] = result

    return TutorMessageResponse(
        message=result["messages"][-1].content,
        current_phase=result["current_phase"],
        attempt_count=result["attempt_count"],
        is_complete=result["is_complete"],
    )

@router.get("/tutor/start", response_model=TutorMessageResponse)
async def start_session(session_id: str):
    state = _new_session_state(session_id)
    opening_line = PHASE_CONTENT["elenchus"][0]

    state["messages"] = [{"role": "assistant", "content": opening_line}]
    _sessions[session_id] = state

    return TutorMessageResponse(
        message=opening_line,
        current_phase=state["current_phase"],
        attempt_count=state["attempt_count"],
        is_complete=state["is_complete"],
    )