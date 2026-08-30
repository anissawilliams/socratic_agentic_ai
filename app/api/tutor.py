from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.graph.graph import tutor_graph
from app.graph.state import TutorState, TutorCondition
from app.socratic.phases import SocraticPhase
from app.socratic.prompts import PHASE_CONTENT


router = APIRouter()


# Temporary in-memory session store.
# Persistent research/event logging is handled separately in Supabase.
_sessions: dict[str, TutorState] = {}


class TutorMessageRequest(BaseModel):
    session_id: UUID
    message: str


class TutorMessageResponse(BaseModel):
    session_id: UUID
    message: str
    current_phase: str | None
    phase_attempt_count: int
    is_complete: bool


def _new_session_state(session_id: str) -> TutorState:
    return {
        "session_id": session_id,
        "messages": [],
        "tutor_condition": TutorCondition.SOCRATIC,

        "current_phase": SocraticPhase.ELENCHUS,
        "previous_phase": None,

        "phase_attempt_count": 0,
        "last_student_message": "",

        "response_evaluation": {
            "hedging_detected": False,
        },

        "pending_event": None,

        "is_complete": False,
        "completed_at": None,
    }


@router.get(
    "/tutor/start",
    response_model=TutorMessageResponse,
)
async def start_session():
    session_id = uuid4()
    session_key = str(session_id)

    state = _new_session_state(session_key)

    opening_line = PHASE_CONTENT[SocraticPhase.ELENCHUS][0]

    state["messages"] = [
        {
            "role": "assistant",
            "content": opening_line,
        }
    ]

    _sessions[session_key] = state

    return TutorMessageResponse(
        session_id=session_id,
        message=opening_line,
        current_phase=state["current_phase"].value,
        phase_attempt_count=state["phase_attempt_count"],
        is_complete=state["is_complete"],
    )


@router.post(
    "/tutor/message",
    response_model=TutorMessageResponse,
)
async def send_message(req: TutorMessageRequest):
    session_key = str(req.session_id)

    state = _sessions.get(session_key)

    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found. Start a new tutoring session.",
        )

    state["last_student_message"] = req.message

    state["messages"] = [
        *state.get("messages", []),
        {
            "role": "user",
            "content": req.message,
        },
    ]

    result = tutor_graph.invoke(state)

    _sessions[session_key] = result

    current_phase = result["current_phase"]

    return TutorMessageResponse(
        session_id=req.session_id,
        message=result["messages"][-1].content,
        current_phase=(
            current_phase.value
            if current_phase is not None
            else None
        ),
        phase_attempt_count=result["phase_attempt_count"],
        is_complete=result["is_complete"],
    )