from fastapi import Header, HTTPException

from app.services.auth import request_access
from app.services.supabase import get_supabase_client


def require_participant(
    authorization: str | None = Header(default=None),
) -> dict:
    """Resolve a bearer token to an enrolled participant, or refuse the request.

    Every route that spends model budget or touches study data depends on this.
    Authenticating with Supabase is not sufficient on its own: the account must
    also be enrolled in the study.
    """
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
