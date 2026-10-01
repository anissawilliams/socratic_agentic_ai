"""Server-authoritative phase timers (pretest, tutor, posttest).

The browser only displays a countdown. Start times, limits, and expiry are
decided by the database, so refreshing, switching tabs, or a wrong laptop
clock can never reset or extend a phase.
"""

from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field

from app.api.assessments import _instrument_key, _scenario_key
from app.api.auth.dependencies import require_participant
from app.config import PHASE_MIN_SECONDS, PHASE_TIME_LIMITS_SECONDS
from app.content.assessments import load_assessment_instrument
from app.services.assignment import current_study_participation
from app.services.supabase import get_supabase_client


router = APIRouter(prefix="/study/timer", tags=["timer"])

TIMED_PHASES = ("pretest", "tutor", "posttest")


def _scalar(data):
    if isinstance(data, list):
        if not data:
            return None
        first = data[0]
        if isinstance(first, dict) and len(first) == 1:
            return next(iter(first.values()))
        return first
    return data


def _participation(participant: dict):
    try:
        return current_study_participation(str(participant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


# ------------------------------------------------------------------ read

class TimerResponse(BaseModel):
    phase: str
    started_at: str
    min_time_seconds: int
    time_limit_seconds: int
    server_now: str


@router.get("", response_model=TimerResponse)
def get_timer(participant: dict = Depends(require_participant)):
    participation = _participation(participant)
    phase = participation.status

    if phase not in TIMED_PHASES:
        raise HTTPException(status_code=404, detail="This step is not timed.")

    rows = get_supabase_client().rpc(
        "get_phase_timer",
        {
            "p_participant_id": str(participant["id"]),
            "p_phase": phase,
            "p_time_limit_seconds": PHASE_TIME_LIMITS_SECONDS[phase],
            "p_min_time_seconds": PHASE_MIN_SECONDS[phase],
        },
    ).execute().data or []

    if isinstance(rows, dict):
        rows = [rows]
    if not rows:
        # The attempt or session hasn't been created yet; the client retries.
        raise HTTPException(status_code=404, detail="Timer has not started yet.")

    row = rows[0]
    return TimerResponse(
        phase=phase,
        started_at=str(row["started_at"]),
        min_time_seconds=int(row["min_time_seconds"] or 0),
        time_limit_seconds=int(row["time_limit_seconds"]),
        server_now=str(row["server_now"]),
    )


# ----------------------------------------------------------- tutor expiry

class ExpiredResponse(BaseModel):
    ended_at: str | None


@router.post("/expire-tutor", response_model=ExpiredResponse)
def expire_tutor(participant: dict = Depends(require_participant)):
    try:
        ended_at = _scalar(
            get_supabase_client().rpc(
                "expire_tutor_session",
                {"p_participant_id": str(participant["id"])},
            ).execute().data
        )
    except APIError as exc:
        raise HTTPException(status_code=409, detail="Time is not up yet.") from exc
    return ExpiredResponse(ended_at=str(ended_at) if ended_at else None)


@router.post("/finish-tutor", response_model=ExpiredResponse)
def finish_tutor(participant: dict = Depends(require_participant)):
    """Participant chooses to move on after the tutor minimum time."""
    try:
        ended_at = _scalar(
            get_supabase_client().rpc(
                "finish_tutor_session",
                {"p_participant_id": str(participant["id"])},
            ).execute().data
        )
    except APIError as exc:
        raise HTTPException(
            status_code=409, detail="You can continue once the minimum time has passed."
        ) from exc
    return ExpiredResponse(ended_at=str(ended_at) if ended_at else None)


# ------------------------------------------------------ assessment expiry

class TimeoutAnswer(BaseModel):
    question_id: str
    value: str = ""  # blank allowed: the student may not have answered


class TimeoutSubmission(BaseModel):
    instrument_key: str
    attempt_id: UUID
    stage: str
    answers: list[TimeoutAnswer] = Field(min_length=4, max_length=4)


@router.post("/submit-assessment", response_model=ExpiredResponse)
def submit_assessment_on_timeout(
    submission: TimeoutSubmission,
    participant: dict = Depends(require_participant),
):
    participation = _participation(participant)

    if submission.stage not in ("pretest", "posttest"):
        raise HTTPException(status_code=422, detail="Unknown assessment stage.")

    if participation.status != submission.stage:
        # Already submitted (normally or by an earlier timeout): nothing to do.
        return ExpiredResponse(ended_at=None)

    instrument_key = _instrument_key(participation, submission.stage)
    if submission.instrument_key != instrument_key:
        raise HTTPException(status_code=409, detail="Assessment does not match assignment.")

    instrument = load_assessment_instrument(instrument_key)
    content = instrument.pretest if submission.stage == "pretest" else instrument.posttest
    if content.scenario_key != _scenario_key(participation, submission.stage):
        raise HTTPException(status_code=409, detail="Assessment does not match assignment.")

    answers = {answer.question_id: answer.value for answer in submission.answers}
    question_ids = [question.id for question in content.questions]
    if set(answers) != set(question_ids):
        raise HTTPException(status_code=422, detail="Assessment answers do not match.")

    try:
        submitted_at = _scalar(
            get_supabase_client().rpc(
                "submit_assessment_on_timeout",
                {
                    "p_attempt_id": str(submission.attempt_id),
                    "p_participant_id": str(participant["id"]),
                    "p_submission_id": str(uuid4()),
                    "p_question_ids": question_ids,
                    "p_construct_codes": [q.construct for q in content.questions],
                    "p_response_texts": [answers[qid].strip() for qid in question_ids],
                },
            ).execute().data
        )
    except APIError as exc:
        raise HTTPException(status_code=409, detail="Time is not up yet.") from exc

    return ExpiredResponse(ended_at=str(submitted_at))


# --------------------------------------------------------- tutor guards

def _tutor_elapsed(session_id: str):
    from datetime import datetime, timezone

    rows = (
        get_supabase_client()
        .table("tutor_session")
        .select("started_at,min_time_seconds,time_limit_seconds,status")
        .eq("id", session_id)
        .limit(1)
        .execute()
        .data
        or []
    )
    if not rows:
        return None, None
    session = rows[0]
    started = datetime.fromisoformat(str(session["started_at"]).replace("Z", "+00:00"))
    elapsed = (datetime.now(timezone.utc) - started).total_seconds()
    return session, elapsed


def tutor_time_is_up(session_id: str) -> bool:
    """True once the tutor session has ended or passed its time limit."""
    session, elapsed = _tutor_elapsed(session_id)
    if session is None:
        return False
    if session["status"] != "active":
        return True
    limit = session.get("time_limit_seconds")
    return bool(limit) and elapsed >= int(limit)


def tutor_min_time_reached(session_id: str) -> bool:
    """False until the tutor minimum has passed; the evaluator can't end it before."""
    session, elapsed = _tutor_elapsed(session_id)
    if session is None:
        return True
    minimum = session.get("min_time_seconds")
    if minimum is None:
        minimum = PHASE_MIN_SECONDS["tutor"]
    return elapsed >= int(minimum)
