from fastapi import Header, HTTPException

from app.db.participants import get_participant_by_study_code


def require_participant(
    participant_code: str | None = Header(
        default=None,
        alias="X-Participant-Code",
    ),
) -> dict:
    """Resolve a study code to an enrolled participant."""

    if not participant_code or not participant_code.strip():
        raise HTTPException(
            status_code=401,
            detail="X-Participant-Code header is required",
        )

    participant = get_participant_by_study_code(participant_code)

    if not participant:
        raise HTTPException(
            status_code=403,
            detail="Participant not authorized",
        )

    return participant
