import hashlib

from app.services.supabase import get_supabase_client


def normalize_study_code(code: str) -> str:
    return "".join(
        character
        for character in code.strip().upper()
        if character.isalnum()
    )


def hash_study_code(code: str) -> str:
    normalized = normalize_study_code(code)

    if not normalized:
        raise ValueError("Access code is required")

    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def get_participant_by_study_code(code: str):
    """Return the participant identified by an existing study code."""
    supabase = get_supabase_client()
    code_hash = hash_study_code(code)

    response = (
        supabase
        .table("study_participant")
        .select("id, email, condition")
        .eq("access_code_hash", code_hash)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]
