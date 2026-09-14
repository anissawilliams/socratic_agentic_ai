from fastapi import Header, HTTPException

from app.services.auth import request_access
from app.services.supabase import get_supabase_client
import os

DEV_AUTH_BYPASS = os.getenv("DEV_AUTH_BYPASS", "false").lower() == "true"
DEV_PARTICIPANT_EMAIL = os.getenv("DEV_PARTICIPANT_EMAIL")
APP_ENV = os.getenv("APP_ENV", "").lower()

_DEV_PARTICIPANT: dict | None = None

def require_participant(
    authorization: str | None = Header(default=None),
) -> dict:
    """Resolve a bearer token to an enrolled participant, or refuse the request."""

    global _DEV_PARTICIPANT

    if DEV_AUTH_BYPASS:
        if APP_ENV != "development":
            raise HTTPException(
                status_code=503,
                detail="Authentication bypass is only allowed in development",
            )

        if not DEV_PARTICIPANT_EMAIL:
            raise HTTPException(
                status_code=503,
                detail="DEV_PARTICIPANT_EMAIL is not configured",
            )

        if _DEV_PARTICIPANT is not None:
            return _DEV_PARTICIPANT

        try:
            _DEV_PARTICIPANT = request_access(
                DEV_PARTICIPANT_EMAIL
            )
            return _DEV_PARTICIPANT
        except ValueError:
            raise HTTPException(
                status_code=403,
                detail="Development participant is not enrolled",
            ) from None

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
        ) from None