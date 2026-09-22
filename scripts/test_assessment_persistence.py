"""Unit checks for typed four-response assessment persistence."""

from dataclasses import dataclass
from uuid import UUID

from app.content.assessments import load_assessment_instrument
from app.persistence import assessments


ATTEMPT_ID = UUID("00000000-0000-0000-0000-000000000010")
PARTICIPATION_ID = UUID("00000000-0000-0000-0000-000000000011")
IDEMPOTENCY_ID = UUID("00000000-0000-0000-0000-000000000012")
SUBMISSION_ID = UUID("00000000-0000-0000-0000-000000000013")
ABANDONMENT_ID = UUID("00000000-0000-0000-0000-000000000014")


@dataclass
class FakeResponse:
    data: object


class FakeRpc:
    def __init__(self, client, name, params):
        self.client = client
        self.name = name
        self.params = params

    def execute(self):
        self.client.calls.append((self.name, self.params))
        if self.name == "start_assessment_attempt":
            return FakeResponse(str(ATTEMPT_ID))
        return FakeResponse("2026-09-17T20:00:00+00:00")


class FakeClient:
    def __init__(self):
        self.calls = []

    def rpc(self, name, params):
        return FakeRpc(self, name, params)


def test_start_and_submit():
    instrument = load_assessment_instrument(
        "near_transfer_template",
        allow_draft=True,
    )
    client = FakeClient()
    original = assessments.get_supabase_client
    assessments.get_supabase_client = lambda: client
    try:
        attempt_id = assessments.start_assessment_attempt(
            attempt_id=ATTEMPT_ID,
            participant_id="00000000-0000-0000-0000-000000000001",
            study_participation_id=PARTICIPATION_ID,
            stage="pretest",
            instrument=instrument,
            attempt_number=1,
            idempotency_key=IDEMPOTENCY_ID,
        )
        answers = {
            question.id: f"Response {index}"
            for index, question in enumerate(
                instrument.pretest.questions,
                start=1,
            )
        }
        submitted_at = assessments.submit_assessment_attempt(
            attempt_id=attempt_id,
            participant_id="00000000-0000-0000-0000-000000000001",
            submission_id=SUBMISSION_ID,
            stage="pretest",
            instrument=instrument,
            answers=answers,
        )
    finally:
        assessments.get_supabase_client = original

    assert attempt_id == ATTEMPT_ID
    assert submitted_at.isoformat() == "2026-09-17T20:00:00+00:00"
    assert client.calls[0][0] == "start_assessment_attempt"
    assert client.calls[0][1]["p_attempt_number"] == 1
    assert client.calls[0][1]["p_scenario_sha256"] != instrument.sha256
    assert client.calls[1][0] == "submit_assessment_attempt"
    submit_params = client.calls[1][1]
    assert len(submit_params["p_question_ids"]) == 4
    assert len(submit_params["p_construct_codes"]) == 4
    assert len(submit_params["p_response_texts"]) == 4
    assert all(not isinstance(value, dict) for value in submit_params.values())


def test_rejects_mismatched_questions():
    instrument = load_assessment_instrument(
        "near_transfer_template",
        allow_draft=True,
    )
    try:
        assessments.submit_assessment_attempt(
            attempt_id=ATTEMPT_ID,
            participant_id="00000000-0000-0000-0000-000000000001",
            submission_id=SUBMISSION_ID,
            stage="pretest",
            instrument=instrument,
            answers={"wrong_question": "Response"},
        )
    except ValueError as exc:
        assert "do not match" in str(exc)
    else:
        raise AssertionError("mismatched question IDs were accepted")


def test_abandonment_is_explicit():
    client = FakeClient()
    original = assessments.get_supabase_client
    assessments.get_supabase_client = lambda: client
    try:
        abandoned_at = assessments.abandon_assessment_attempt(
            attempt_id=ATTEMPT_ID,
            participant_id="00000000-0000-0000-0000-000000000001",
            abandonment_id=ABANDONMENT_ID,
            reason_code="participant_exit",
        )
    finally:
        assessments.get_supabase_client = original

    assert abandoned_at.isoformat() == "2026-09-17T20:00:00+00:00"
    assert client.calls[0][0] == "abandon_assessment_attempt"
    assert client.calls[0][1]["p_reason_code"] == "participant_exit"


if __name__ == "__main__":
    test_start_and_submit()
    test_rejects_mismatched_questions()
    test_abandonment_is_explicit()
    print("ok")
