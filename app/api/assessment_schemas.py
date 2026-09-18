"""API contract for standalone pre/post-test submissions."""

from enum import Enum

from pydantic import BaseModel, Field


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
    scenario_key: str
    scenario_version: str
    scenario_sha256: str
    scenario_title: str
    scenario_text: str
    questions: list[AssessmentQuestionResponse]


class AssessmentAnswer(BaseModel):
    question_id: str
    value: str = Field(min_length=1)


class AssessmentSubmission(BaseModel):
    instrument_key: str
    instrument_version: str
    content_sha256: str
    stage: AssessmentStage
    scenario_key: str
    answers: list[AssessmentAnswer] = Field(min_length=4, max_length=4)


class AssessmentSubmissionResponse(BaseModel):
    submission_id: str
    submitted_at: str
