from fastapi import APIRouter, Depends

from app.api.auth.dependencies import require_participant
from app.api.auth.schemas import ParticipantResponse
from app.services.assignment import current_study_participation


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get(
    "/me",
    response_model=ParticipantResponse,
)
def get_current_participant(
    participant: dict = Depends(require_participant),
) -> dict:
    participation = current_study_participation(
        str(participant["id"])
    )

    return {
        **participant,
        "study_status": participation.status,
    }