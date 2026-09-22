"""Typed assessment persistence backed by transactional database functions."""

from datetime import datetime
from uuid import UUID

from app.content.assessments import AssessmentInstrument, AssessmentStage
from app.services.supabase import get_supabase_client


def _rpc_scalar(data):
    if isinstance(data, list):
        if not data:
            return None
        first = data[0]
        if isinstance(first, dict) and len(first) == 1:
            return next(iter(first.values()))
        return first
    return data


def _stage_content(
    instrument: AssessmentInstrument,
    stage: AssessmentStage,
):
    return instrument.pretest if stage == "pretest" else instrument.posttest


def start_assessment_attempt(
    *,
    attempt_id: UUID,
    participant_id: str,
    study_participation_id: UUID,
    stage: AssessmentStage,
    instrument: AssessmentInstrument,
    attempt_number: int,
    idempotency_key: UUID,
) -> UUID:
    """Start or recover one idempotent assessment attempt."""
    content = _stage_content(instrument, stage)
    response = get_supabase_client().rpc(
        "start_assessment_attempt",
        {
            "p_attempt_id": str(attempt_id),
            "p_participant_id": participant_id,
            "p_study_participation_id": str(study_participation_id),
            "p_stage": stage,
            "p_instrument_key": instrument.key,
            "p_instrument_version": instrument.version,
            "p_content_sha256": instrument.sha256,
            "p_scenario_key": content.scenario_key,
            "p_scenario_version": content.scenario_version,
            "p_scenario_sha256": content.scenario_sha256,
            "p_attempt_number": attempt_number,
            "p_idempotency_key": str(idempotency_key),
        },
    ).execute()
    return UUID(str(_rpc_scalar(response.data)))


def submit_assessment_attempt(
    *,
    attempt_id: UUID,
    participant_id: str,
    submission_id: UUID,
    stage: AssessmentStage,
    instrument: AssessmentInstrument,
    answers: dict[str, str],
) -> datetime:
    """Persist exactly four ordered open-text answers atomically."""
    content = _stage_content(instrument, stage)
    expected_ids = [question.id for question in content.questions]
    if set(answers) != set(expected_ids):
        missing = sorted(set(expected_ids) - set(answers))
        unexpected = sorted(set(answers) - set(expected_ids))
        raise ValueError(
            "Assessment answer IDs do not match the instrument; "
            f"missing={missing}, unexpected={unexpected}"
        )

    response_texts = [answers[question_id].strip() for question_id in expected_ids]
    if any(not response for response in response_texts):
        raise ValueError("Assessment answers cannot be blank")

    response = get_supabase_client().rpc(
        "submit_assessment_attempt",
        {
            "p_attempt_id": str(attempt_id),
            "p_participant_id": participant_id,
            "p_submission_id": str(submission_id),
            "p_question_ids": expected_ids,
            "p_construct_codes": [
                question.construct for question in content.questions
            ],
            "p_response_texts": response_texts,
        },
    ).execute()
    submitted_at = _rpc_scalar(response.data)
    return datetime.fromisoformat(str(submitted_at).replace("Z", "+00:00"))


def abandon_assessment_attempt(
    *,
    attempt_id: UUID,
    participant_id: str,
    abandonment_id: UUID,
    reason_code: str,
) -> datetime:
    """Retain an interrupted attempt and release the stage for a retry."""
    if not reason_code.strip():
        raise ValueError("Assessment abandonment reason is required")
    response = get_supabase_client().rpc(
        "abandon_assessment_attempt",
        {
            "p_attempt_id": str(attempt_id),
            "p_participant_id": participant_id,
            "p_abandonment_id": str(abandonment_id),
            "p_reason_code": reason_code.strip(),
        },
    ).execute()
    abandoned_at = _rpc_scalar(response.data)
    return datetime.fromisoformat(str(abandoned_at).replace("Z", "+00:00"))
