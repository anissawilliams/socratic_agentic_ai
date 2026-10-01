"""Round 1 demographics and Round 2 final survey.

Both forms are thin wrappers around idempotent database functions
(submit_demographics, submit_final_survey) that also advance the study
status, so a double-submit or a refresh can never create duplicates.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

import yaml
from fastapi import APIRouter, Depends, HTTPException
from postgrest.exceptions import APIError
from pydantic import BaseModel, Field, model_validator

from app.api.auth.dependencies import require_participant
from app.services.assignment import current_study_participation
from app.services.supabase import get_supabase_client


router = APIRouter(prefix="/study", tags=["study-forms"])

SURVEY_PATH = (
    Path(__file__).resolve().parents[2] / "content" / "surveys" / "final_survey.yaml"
)

GenderCode = Literal["male", "female", "non_binary"]

AcademicLevelCode = Literal["undergraduate", "graduate"]

RaceCode = Literal[
    "white_european",
    "black_african",
    "asian",
    "hispanic_latino",
    "middle_eastern_north_african",
    "other",
]


# ---------------------------------------------------------------- helpers

def _participation_at(participant: dict, expected_status: str):
    try:
        participation = current_study_participation(str(participant["id"]))
    except ValueError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc

    if participation.status != expected_status:
        raise HTTPException(
            status_code=409,
            detail="This step is not available right now.",
        )
    return participation


def _rpc(name: str, params: dict):
    try:
        return get_supabase_client().rpc(name, params).execute().data
    except APIError as exc:
        # Constraint or stage errors raised by the database function.
        raise HTTPException(
            status_code=422,
            detail="Your responses could not be saved. Please check them and try again.",
        ) from exc


@lru_cache
def _survey() -> dict:
    with SURVEY_PATH.open(encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if len(data.get("likert", [])) != 4:
        raise ValueError("final_survey.yaml must define exactly 4 Likert items")
    return data


# ------------------------------------------------------------ demographics

class DemographicsSubmission(BaseModel):
    age: int = Field(ge=18, le=99)
    gender_code: GenderCode
    academic_level_code: AcademicLevelCode
    race_codes: list[RaceCode] = Field(min_length=1)
    race_other_description: str | None = Field(default=None, max_length=100)
    field_of_study: str = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def _other_description_matches(self):
        self.race_codes = sorted(set(self.race_codes))
        text = (self.race_other_description or "").strip()
        if "other" in self.race_codes and not text:
            raise ValueError("Please describe your background or unselect that option.")
        self.race_other_description = text if "other" in self.race_codes else None
        self.field_of_study = self.field_of_study.strip()
        if not self.field_of_study:
            raise ValueError("Please enter your field of study.")
        return self


class SubmittedResponse(BaseModel):
    submitted_at: str


@router.post("/demographics", response_model=SubmittedResponse)
def submit_demographics(
    submission: DemographicsSubmission,
    participant: dict = Depends(require_participant),
):
    _participation_at(participant, "demographics")
    submitted_at = _rpc(
        "submit_demographics",
        {
            "p_participant_id": str(participant["id"]),
            "p_age": submission.age,
            "p_gender_code": submission.gender_code,
            "p_academic_level_code": submission.academic_level_code,
            **{
                f"p_race_{code}": code in submission.race_codes
                for code in RaceCode.__args__
            },
            "p_race_other_description": submission.race_other_description,
            "p_field_of_study": submission.field_of_study,
        },
    )
    return SubmittedResponse(submitted_at=str(submitted_at))


# ------------------------------------------------------------ final survey

class SurveyItem(BaseModel):
    id: str
    prompt: str


class SurveyContent(BaseModel):
    instrument_key: str
    instrument_version: str
    scale: list[str]
    likert: list[SurveyItem]
    open: SurveyItem


class SurveySubmission(BaseModel):
    instrument_key: str
    instrument_version: str
    likert: list[int] = Field(min_length=4, max_length=4)
    open_response: str | None = Field(default=None, max_length=5000)

    @model_validator(mode="after")
    def _likert_range(self):
        if any(value < 1 or value > 5 for value in self.likert):
            raise ValueError("Each rating must be between 1 and 5.")
        return self


@router.get("/survey", response_model=SurveyContent)
def get_survey(participant: dict = Depends(require_participant)):
    _participation_at(participant, "survey")
    survey = _survey()
    return SurveyContent(
        instrument_key=survey["key"],
        instrument_version=survey["version"],
        scale=survey["scale"],
        likert=survey["likert"],
        open=survey["open"],
    )


@router.post("/survey", response_model=SubmittedResponse)
def submit_survey(
    submission: SurveySubmission,
    participant: dict = Depends(require_participant),
):
    _participation_at(participant, "survey")
    survey = _survey()
    if (
        submission.instrument_key != survey["key"]
        or submission.instrument_version != survey["version"]
    ):
        raise HTTPException(
            status_code=409,
            detail="The survey was updated. Please refresh the page.",
        )

    l1, l2, l3, l4 = submission.likert
    submitted_at = _rpc(
        "submit_final_survey",
        {
            "p_participant_id": str(participant["id"]),
            "p_instrument_key": submission.instrument_key,
            "p_instrument_version": submission.instrument_version,
            "p_likert_1": l1,
            "p_likert_2": l2,
            "p_likert_3": l3,
            "p_likert_4": l4,
            "p_open_response": submission.open_response,
        },
    )
    return SubmittedResponse(submitted_at=str(submitted_at))
