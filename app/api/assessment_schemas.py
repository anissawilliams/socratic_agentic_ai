"""API contract for standalone pre/post-test submissions."""

from enum import Enum

from pydantic import BaseModel, Field, field_validator

MIN_ANSWER_WORDS = 5


class AssessmentStage(str, Enum):
    PRETEST = "pretest"
    POSTTEST = "posttest"


class AssessmentQuestionResponse(BaseModel):
    id: str
    construct: str
    prompt: str


class AssessmentContentResponse(BaseModel):
    instrument_key: str
    instrument_version: str
    content_sha256: str
    stage: AssessmentStage
    attempt_id: str
    scenario_key: str
    scenario_version: str
    scenario_sha256: str
    scenario_title: str
    scenario_text: str
    questions: list[AssessmentQuestionResponse]


class AssessmentAnswer(BaseModel):
    question_id: str
    value: str = Field(min_length=1)

    @field_validator("value")
    @classmethod
    def _minimum_words(cls, value: str) -> str:
        # Normal submissions need at least five words per answer. Timeout
        # submissions use a separate schema and save whatever was written.
        if len(value.split()) < MIN_ANSWER_WORDS:
            raise ValueError(
                f"Please write at least {MIN_ANSWER_WORDS} words for each answer."
            )
        return value


class AssessmentSubmission(BaseModel):
    instrument_key: str
    instrument_version: str
    attempt_id: str
    content_sha256: str
    stage: AssessmentStage
    scenario_key: str
    answers: list[AssessmentAnswer] = Field(min_length=4, max_length=4)


class AssessmentSubmissionResponse(BaseModel):
    submission_id: str
    submitted_at: str
