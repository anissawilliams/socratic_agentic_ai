from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException

from app.api.assessment_schemas import (
    AssessmentContentResponse,
    AssessmentQuestionResponse,
    AssessmentSubmission,
    AssessmentSubmissionResponse,
)
from app.api.auth.dependencies import require_participant
from app.content.assessments import load_assessment_instrument
from app.persistence.assessments import (
    start_assessment_attempt,
    submit_assessment_attempt,
)
from app.services.assignment import current_study_participation


router = APIRouter(
    prefix="/assessment",
    tags=["assessment"],
)


def _instrument_key(participation, stage: str) -> str:
    if stage == "pretest":
        return participation.pretest_instrument_key

    if stage == "posttest":
        return participation.posttest_instrument_key

    raise ValueError(f"Unsupported assessment stage: {stage}")

def _scenario_key(participation, stage: str) -> str:
    if stage == "pretest":
        return participation.pretest_scenario_key
    if stage == "posttest":
        return participation.posttest_scenario_key
    raise ValueError(f"Unsupported assessment stage: {stage}")

@router.post(
    "/start",
    response_model=AssessmentContentResponse,
)
def start_assessment(
    participant: dict = Depends(require_participant),
):
    try:
        participation = current_study_participation(
            str(participant["id"])
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    stage = participation.status

    if stage not in {"pretest", "posttest"}:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Participant study stage is {stage!r}; "
                "no assessment is currently available"
            ),
        )

    instrument_key = _instrument_key(
        participation,
        stage,
    )

    try:
        instrument = load_assessment_instrument(
            instrument_key
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    content = (
        instrument.pretest
        if stage == "pretest"
        else instrument.posttest
    )

    assigned_scenario_key = _scenario_key(
    participation,
    stage,
)

    if content.scenario_key != assigned_scenario_key:
        raise HTTPException(
            status_code=409,
            detail="Assessment scenario does not match study assignment",
        )
    


    try:
        attempt_id = start_assessment_attempt(
            attempt_id=uuid4(),
            participant_id=str(participant["id"]),
            study_participation_id=UUID(
                participation.id
            ),
            stage=stage,
            instrument=instrument,
            attempt_number=1,
            idempotency_key=uuid4(),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return AssessmentContentResponse(
        attempt_id=str(attempt_id),
        instrument_key=instrument.key,
        instrument_version=instrument.version,
        content_sha256=instrument.sha256,
        stage=stage,
        scenario_key=content.scenario_key,
        scenario_version=content.scenario_version,
        scenario_sha256=content.scenario_sha256,
        scenario_title=content.scenario_title,
        scenario_text=content.scenario_text,
        questions=[
            AssessmentQuestionResponse(
                id=question.id,
                construct=question.construct,
                prompt=question.prompt,
            )
            for question in content.questions
        ],
    )


@router.post(
    "/submit",
    response_model=AssessmentSubmissionResponse,
)

def submit_assessment(
    submission: AssessmentSubmission,
    participant: dict = Depends(require_participant),
):
    try:
        participation = current_study_participation(
            str(participant["id"])
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403,
            detail=str(exc),
        ) from exc

    stage = submission.stage.value

    if participation.status != stage:
        raise HTTPException(
            status_code=409,
            detail=(
                f"Participant study stage is "
                f"{participation.status!r}, not {stage!r}"
            ),
        )

    instrument_key = _instrument_key(
        participation,
        stage,
    )

    if submission.instrument_key != instrument_key:
        raise HTTPException(
            status_code=409,
            detail="Assessment instrument does not match study assignment",
        )

    try:
        instrument = load_assessment_instrument(
            instrument_key
        )
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        ) from exc

    content = (
        instrument.pretest
        if stage == "pretest"
        else instrument.posttest
    )

    assigned_scenario_key = _scenario_key(
        participation,
        stage,
    )

    if content.scenario_key != assigned_scenario_key:
        raise HTTPException(
            status_code=409,
            detail="Assessment scenario does not match study assignment",
        )

    if (
        submission.instrument_version != instrument.version
        or submission.content_sha256 != instrument.sha256
        or submission.scenario_key != content.scenario_key
    ):
        raise HTTPException(
            status_code=409,
            detail="Assessment content no longer matches assigned version",
        )

    submission_id = uuid4()

    try:
        submitted_at = submit_assessment_attempt(
            attempt_id=UUID(submission.attempt_id),
            participant_id=str(participant["id"]),
            submission_id=submission_id,
            stage=stage,
            instrument=instrument,
            answers={
                answer.question_id: answer.value
                for answer in submission.answers
            },
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return AssessmentSubmissionResponse(
        submission_id=str(submission_id),
        submitted_at=submitted_at.isoformat(),
    ) 