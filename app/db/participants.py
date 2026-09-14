import hashlib

from app.services.supabase import get_supabase_client


def _normalize_access_code(code: str) -> str:
    return "".join(
        character
        for character in code.strip().upper()
        if character.isalnum()
    )


def _hash_access_code(code: str) -> str:
    normalized = _normalize_access_code(code)

    if not normalized:
        raise ValueError("Access code is required")

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_participant_by_email(email: str):
    """Development-only participant lookup used by the auth bypass."""
    supabase = get_supabase_client()

    response = (
        supabase
        .table("study_participant")
        .select("id, email, condition")
        .eq("email", email)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def get_participant_by_auth_user_id(auth_user_id: str):
    """Resolve an authenticated Supabase user to its claimed participant."""
    supabase = get_supabase_client()

    response = (
        supabase
        .table("study_participant")
        .select("id, email, condition, auth_user_id")
        .eq("auth_user_id", auth_user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def claim_participant_by_access_code(
    code: str,
    auth_user_id: str,
):
    """Claim an access code for this authenticated Supabase user.

    A code may be claimed once. Repeating the claim from the same
    authenticated user is idempotent.
    """
    supabase = get_supabase_client()
    code_hash = _hash_access_code(code)

    response = (
        supabase
        .table("study_participant")
        .select(
            "id, email, condition, auth_user_id, access_code_hash"
        )
        .eq("access_code_hash", code_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise ValueError("Invalid participant code")

    participant = response.data[0]
    existing_auth_user_id = participant.get("auth_user_id")

    if existing_auth_user_id:
        if existing_auth_user_id == auth_user_id:
            return participant

        raise PermissionError(
            "Participant code has already been claimed"
        )

    update = (
        supabase
        .table("study_participant")
        .update({"auth_user_id": auth_user_id})
        .eq("id", participant["id"])
        .is_("auth_user_id", "null")
        .execute()
    )

    if update.data:
        return update.data[0]

    # Protect against a race where another request claimed the code
    # between the SELECT and UPDATE.
    refreshed = (
        supabase
        .table("study_participant")
        .select("id, email, condition, auth_user_id")
        .eq("id", participant["id"])
        .limit(1)
        .execute()
    )

    if not refreshed.data:
        raise RuntimeError("Participant disappeared during code claim")

    participant = refreshed.data[0]

    if participant.get("auth_user_id") == auth_user_id:
        return participant

    raise PermissionError(
        "Participant code has already been claimed"
    )