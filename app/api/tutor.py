from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.api.auth.dependencies import require_participant
from app.content.scenarios import load_scenario
from app.graph.graph import tutor_graph
from app.graph.state import TutorState, TutorCondition
from app.services.condition import tutor_condition_for_participant
from app.socratic.phases import SocraticPhase


router = APIRouter()

_sessions: dict[str, TutorState] = {}


class TutorMessageRequest(BaseModel):
    session_id: UUID
    message: str


class TutorMessageResponse(BaseModel):
    session_id: UUID
    current_turn_id: UUID | None
    message: str
    current_phase: str | None
    is_complete: bool


def _new_session_state(
    session_id: str,
    participant: dict,
) -> TutorState:
    initial_phase = SocraticPhase.ELENCHUS

    return {
        "session_id": session_id,
        "participant_id": str(participant["id"]),
        "messages": [],
        "tutor_condition": tutor_condition_for_participant(
            participant
        ),
        "current_turn_id": None,
        "current_phase": initial_phase,
        "previous_phase": None,
        "phase_history": [initial_phase],
        "route_decision": None,
        "routing_history": [],
        "pending_event": None,
        "last_student_message": "",
        "response_evaluation": None,
        "is_complete": False,
        "completed_at": None,
    }
@router.get(
    "/tutor/start",
    response_model=TutorMessageResponse,
)
async def start_session(
    participant: dict = Depends(require_participant),
):
    session_id = uuid4()
    turn_id = uuid4()
    session_key = str(session_id)
    turn_key = str(turn_id)
    try:
        state = _new_session_state(session_key, participant)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    if state["tutor_condition"] is not TutorCondition.SOCRATIC:
        raise HTTPException(
            status_code=501,
            detail=(
                f"Tutor condition {state['tutor_condition'].value!r} is assigned "
                "but not implemented yet. Only the Socratic arm is active in this build."
            ),
        )

    state["current_turn_id"] = turn_key
    opening_line = load_scenario().opening_question

    state["messages"] = [AIMessage(content=opening_line)]

    _sessions[session_key] = state

    return TutorMessageResponse(
        session_id=session_id,
        message=opening_line,
        current_phase=state["current_phase"].value,
        current_turn_id=state["current_turn_id"],
        is_complete=state["is_complete"],
    )


@router.post(
    "/tutor/message",
    response_model=TutorMessageResponse,
)
async def send_message(
    req: TutorMessageRequest,
    participant: dict = Depends(require_participant),
):
    session_key = str(req.session_id)
    turn_id = uuid4()
    turn_key = str(turn_id)

    state = _sessions.get(session_key)

    # Someone else's session is reported as missing rather than forbidden, so a
    # guessed session ID cannot be used to confirm that a session exists.
    if state is None or state["participant_id"] != str(participant["id"]):
        raise HTTPException(
            status_code=404,
            detail="Session not found. Start a new tutoring session.",
        )

    if state["is_complete"]:
        raise HTTPException(
            status_code=409,
            detail="This tutoring session is complete. Start a new session.",
    )

    state["current_turn_id"] = turn_key
    state["last_student_message"] = req.message

    state["messages"] = [
        *state.get("messages", []),
        HumanMessage(content=req.message),
    ]

    messages_before = len(state["messages"])

    result = tutor_graph.invoke(state)

    _sessions[session_key] = result

    # Return only messages generated during this graph invocation.
    generated = result["messages"][messages_before:]
    tutor_message = generated[-1].content if generated else ""

    current_phase = result["current_phase"]

    return TutorMessageResponse(
        session_id=req.session_id,
        current_turn_id=turn_id,
        message=tutor_message,
        current_phase=(
            current_phase.value
            if current_phase is not None
            else None
        ),
        is_complete=result["is_complete"],
    )