import contextvars
from copy import deepcopy
import json
import logging
import queue
import threading
from time import perf_counter
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import AIMessage, HumanMessage
from pydantic import BaseModel

from app.api.auth.dependencies import require_participant
from app.api.timer import tutor_min_time_reached, tutor_time_is_up
from app.content.scenarios import load_scenario
from app.content.assessments import load_assessment_instrument
from app.control.direct_chat import (
    DIRECT_CHAT_PROMPT_SHA256,
    opening_message as direct_chat_opening,
    respond as direct_chat_respond,
)
from app.graph.graph import tutor_graph
from app.graph.state import TutorState, TutorCondition
from app.services.condition import tutor_condition_for_participant
from app.services.assignment import current_study_participation
from app.services.llm import collect_llm_usage
from app.services.scenario_context import (
    scenario_context_message,
    with_scenario_context,
    without_scenario_context,
)
from app.socratic.phases import SocraticPhase
from app.persistence.sessions import (
    save_direct_chat_turn,
    create_session,
    fail_turn,
    load_session,
    save_turn,
    start_turn,
)


router = APIRouter()
logger = logging.getLogger(__name__)

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
    study_participation_id: str,
) -> TutorState:
    initial_phase = SocraticPhase.ELENCHUS

    return {
        "session_id": session_id,
        "participant_id": str(participant["id"]),
        "study_participation_id": study_participation_id,
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
def start_session(
    participant: dict = Depends(require_participant),
):
    session_id = uuid4()
    turn_id = uuid4()
    session_key = str(session_id)
    turn_key = str(turn_id)
    try:
        participation = current_study_participation(str(participant["id"]))
        if participation.assigned_condition_code != str(participant["condition"]):
            raise ValueError("Participant condition does not match study assignment")
        if participation.status != "tutor":
            raise ValueError(
                f"Participant study stage is {participation.status!r}, not 'tutor'"
            )
        state = _new_session_state(session_key, participant, participation.id)
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    state["current_turn_id"] = turn_key
    try:
        scenario = load_scenario(participation.tutor_scenario_key)
    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=409,
            detail="Assigned tutor scenario is unavailable in this deployment.",
        ) from exc
    try:
        _, scenario_title = scenario_context_message(participation.pretest_instrument_key)
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail="Assigned scenario is unavailable in this deployment.",
        ) from exc
    state["scenario_key"] = participation.tutor_scenario_key

    is_control = state["tutor_condition"] is TutorCondition.DIRECT_CHAT
    if is_control:
        # Student-led: a neutral invitation, no Socratic phases.
        opening_line = direct_chat_opening(scenario_title)
        state["current_phase"] = None
        state["phase_history"] = []
    else:
        opening_line = scenario.opening_question

    state["messages"] = [AIMessage(content=opening_line)]

    create_session(
        state,
        assigned_condition_code=str(participant["condition"]),
        scenario=scenario,
        prompt_sha256=DIRECT_CHAT_PROMPT_SHA256 if is_control else None,
    )

    return TutorMessageResponse(
        session_id=session_id,
        message=opening_line,
        current_phase=state["current_phase"].value if state["current_phase"] else None,
        current_turn_id=state["current_turn_id"],
        is_complete=state["is_complete"],
    )


def _direct_chat_turn(state, req, participant, scenario_context, session_key):
    """Control condition: one assistant reply per turn, no evaluator/router."""
    turn_id = uuid4()
    state = deepcopy(state)
    state["current_turn_id"] = str(turn_id)
    state["last_student_message"] = req.message
    history = [*state.get("messages", []), HumanMessage(content=req.message)]

    start_turn(state, phase_before=None, prompt_sha256=DIRECT_CHAT_PROMPT_SHA256)
    started = perf_counter()
    try:
        with collect_llm_usage() as usage:
            reply = direct_chat_respond(with_scenario_context(history, scenario_context))
        latency_ms = round((perf_counter() - started) * 1000)
        save_direct_chat_turn(
            state,
            tutor_response=reply.text,
            latency_ms=latency_ms,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
    except Exception as exc:
        try:
            fail_turn(
                state,
                exc,
                latency_ms=round((perf_counter() - started) * 1000),
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
        except Exception:
            logger.exception("Failed to persist terminal failure for tutor turn %s", turn_id)
        raise

    state["messages"] = [*history, AIMessage(content=reply.text)]
    _sessions[session_key] = state

    return TutorMessageResponse(
        session_id=req.session_id,
        current_turn_id=turn_id,
        message=reply.text,
        current_phase=None,
        is_complete=False,
    )


class _PreparedTurn:
    """Everything a Socratic turn needs after validation, shared by the
    blocking and streaming endpoints."""

    def __init__(self, *, state, session_key, turn_id, messages_before, phase_before):
        self.state = state
        self.session_key = session_key
        self.turn_id = turn_id
        self.messages_before = messages_before
        self.phase_before = phase_before


def _prepare_turn(
    req: TutorMessageRequest,
    participant: dict,
) -> _PreparedTurn | TutorMessageResponse:
    """Validate the request and build the turn state.

    Returns a finished TutorMessageResponse for the control condition
    (which has no Socratic graph), otherwise a _PreparedTurn whose turn has
    been started in the database.
    """
    if tutor_time_is_up(str(req.session_id)):
        raise HTTPException(status_code=409, detail="time_up")

    session_key = str(req.session_id)
    turn_id = uuid4()
    turn_key = str(turn_id)

    state = _sessions.get(session_key)

    if state is None:
        state = load_session(
            session_key,
            str(participant["id"]),
        )

        if state is not None:
            _sessions[session_key] = state

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

    try:
        participation = current_study_participation(str(participant["id"]))
        scenario_context, _ = scenario_context_message(participation.pretest_instrument_key)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if state["tutor_condition"] is TutorCondition.DIRECT_CHAT:
        return _direct_chat_turn(state, req, participant, scenario_context, session_key)

    # Work on a copy so a failed invocation cannot contaminate the in-memory
    # representation of the last successfully completed turn.
    state = deepcopy(state)
    state["scenario_key"] = participation.tutor_scenario_key
    state["current_turn_id"] = turn_key
    state["last_student_message"] = req.message
    state["min_time_reached"] = tutor_min_time_reached(session_key)
    state["route_decision"] = None
    state["response_evaluation"] = None

    # The scenario text rides along as context for every model call this
    # turn (tutor, evaluator, router). It is stripped before caching.
    state["messages"] = with_scenario_context(
        [*state.get("messages", []), HumanMessage(content=req.message)],
        scenario_context,
    )

    phase_before = state["current_phase"]
    if phase_before is None:
        raise HTTPException(
            status_code=409,
            detail="This tutoring session has no active phase.",
        )

    start_turn(state, phase_before=phase_before)

    return _PreparedTurn(
        state=state,
        session_key=session_key,
        turn_id=turn_id,
        messages_before=len(state["messages"]),
        phase_before=phase_before,
    )


def _run_turn(turn: _PreparedTurn, run_graph) -> TutorMessageResponse:
    """Run the graph via run_graph(state) -> final state, persist, respond."""
    started = perf_counter()
    try:
        with collect_llm_usage() as usage:
            result = run_graph(turn.state)
        latency_ms = round((perf_counter() - started) * 1000)
        save_turn(
            result,
            phase_before=turn.phase_before,
            latency_ms=latency_ms,
            input_tokens=usage.input_tokens,
            output_tokens=usage.output_tokens,
        )
    except Exception as exc:
        try:
            fail_turn(
                turn.state,
                exc,
                latency_ms=round((perf_counter() - started) * 1000),
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
            )
        except Exception:
            logger.exception(
                "Failed to persist terminal failure for tutor turn %s",
                turn.turn_id,
            )
        raise

    # Return only messages generated during this graph invocation.
    generated = result["messages"][turn.messages_before:]
    result["messages"] = without_scenario_context(result["messages"])
    _sessions[turn.session_key] = result
    tutor_message = generated[-1].text if generated else ""

    current_phase = result["current_phase"]

    return TutorMessageResponse(
        session_id=UUID(turn.session_key),
        current_turn_id=turn.turn_id,
        message=tutor_message,
        current_phase=(
            current_phase.value
            if current_phase is not None
            else None
        ),
        is_complete=result["is_complete"],
    )


@router.post(
    "/tutor/message",
    response_model=TutorMessageResponse,
)
def send_message(
    req: TutorMessageRequest,
    participant: dict = Depends(require_participant),
):
    turn = _prepare_turn(req, participant)
    if isinstance(turn, TutorMessageResponse):
        return turn
    return _run_turn(turn, tutor_graph.invoke)


# Nodes whose model tokens are the student-facing tutor reply. Evaluator and
# router tokens (structured JSON) are never streamed to the student.
_STREAMED_NODES = {"generate_response"}


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


@router.post("/tutor/message/stream")
def send_message_stream(
    req: TutorMessageRequest,
    participant: dict = Depends(require_participant),
):
    """Same turn as /tutor/message, delivered as server-sent events.

    Events:
      token  {"text": "..."}         a piece of the tutor reply as it is generated
      done   TutorMessageResponse    the final, persisted turn (authoritative text)
      error  {"detail": "..."}       the turn failed; it was recorded as failed

    Persistence, latency, and token accounting are identical to the blocking
    endpoint: the graph runs in a worker thread through _run_turn.
    """
    # Validation errors (404/409/403) are raised here, before streaming
    # begins, so the client receives a normal HTTP error status.
    turn = _prepare_turn(req, participant)

    events: queue.Queue = queue.Queue()
    _END = object()

    def stream_graph(state):
        final_state = None
        for mode, chunk in tutor_graph.stream(
            state,
            stream_mode=["messages", "values"],
        ):
            if mode == "values":
                final_state = chunk
                continue
            message, metadata = chunk
            if metadata.get("langgraph_node") not in _STREAMED_NODES:
                continue
            text = message.content if isinstance(message.content, str) else ""
            if text:
                events.put(("token", {"text": text}))
        if final_state is None:
            raise RuntimeError("Tutor graph produced no final state.")
        return final_state

    def worker():
        try:
            if isinstance(turn, TutorMessageResponse):
                response = turn
            else:
                response = _run_turn(turn, stream_graph)
            events.put(("done", response.model_dump(mode="json")))
        except Exception:
            logger.exception("Streaming tutor turn failed")
            events.put((
                "error",
                {"detail": "The tutor hit an error while generating a reply."},
            ))
        finally:
            events.put(_END)

    # copy_context keeps request-scoped context (e.g. tracing) in the worker.
    ctx = contextvars.copy_context()
    threading.Thread(target=ctx.run, args=(worker,), daemon=True).start()

    def body():
        while True:
            item = events.get()
            if item is _END:
                return
            event, data = item
            yield _sse(event, data)

    return StreamingResponse(
        body(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Stop proxies (Railway/nginx) from buffering the stream.
            "X-Accel-Buffering": "no",
        },
    )


class TutorScenarioResponse(BaseModel):
    title: str
    text: str


@router.get("/tutor/scenario", response_model=TutorScenarioResponse)
def get_tutor_scenario(participant: dict = Depends(require_participant)):
    """The pretest scenario, shown above the chat in both conditions."""
    try:
        participation = current_study_participation(str(participant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if participation.status != "tutor":
        raise HTTPException(status_code=409, detail="Not at the AI step.")

    content = load_assessment_instrument(participation.pretest_instrument_key).pretest
    return TutorScenarioResponse(title=content.scenario_title, text=content.scenario_text)