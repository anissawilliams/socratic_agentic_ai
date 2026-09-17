from fastapi import APIRouter, Depends

from app.api.auth.dependencies import require_participant
from app.api.auth.schemas import ParticipantResponse

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
    return participant
