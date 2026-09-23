from fastapi import APIRouter, Depends, HTTPException

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
    try:
        participation = current_study_participation(
            str(participant["id"])
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=403, 
            detail=str(exc)
            ) from exc


    return {
        **participant,
        "study_status": participation.status,
    }