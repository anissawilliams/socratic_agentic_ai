from fastapi import APIRouter, Depends, HTTPException

from app.api.auth.dependencies import require_participant, require_auth_user
from app.api.auth.schemas import ParticipantResponse, ParticipanCodeRequest
from app.db.participants import claim_participant_by_access_code

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post(
    "/code",
    response_model=ParticipantResponse,
)
def claim_participant_code(
    request: ParticipanCodeRequest,
    user=Depends(require_auth_user),
) -> dict:
    try:
        return claim_participant_by_access_code(
            request.code,
            str(user.id),
        )
    except (ValueError, PermissionError):
        raise HTTPException(
            status_code=403,
            detail="Invalid or unavailable participant code",
        ) from None


@router.get(
    "/me",
    response_model=ParticipantResponse,
)
def get_current_participant(
    participant: dict = Depends(require_participant),
) -> dict:
    return participant