from fastapi import APIRouter, Header, HTTPException

from app.api.auth.schemas import ParticipantResponse
from app.services.auth import request_access
from app.services.supabase import get_supabase_client


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.get("/me", response_model=ParticipantResponse)
def get_current_participant(
    authorization: str | None = Header(default=None),
):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Missing or invalid authorization header",
        )

    token = authorization.removeprefix("Bearer ").strip()

    supabase = get_supabase_client()

    try:
        user_response = supabase.auth.get_user(token)
        user = user_response.user
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
        )

    if not user or not user.email:
        raise HTTPException(
            status_code=401,
            detail="Authenticated user has no email",
        )

    try:
        return request_access(user.email)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Participant not authorized",
        )