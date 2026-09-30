from fastapi import APIRouter, Depends, HTTPException

from app.api.auth.dependencies import require_participant
from app.api.auth.schemas import ParticipantResponse
from app.services.assignment import current_study_participation
from app.services.supabase import get_supabase_client


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
        # The current-participation RPC excludes completed rounds. A participant
        # who just submitted the post-test still needs a status for the final UI.
        client = get_supabase_client()
        links = (
            client.table("study_subject_identity_link")
            .select("study_subject_id")
            .eq("participant_id", str(participant["id"]))
            .limit(1)
            .execute()
            .data
        )
        completed = []
        if links:
            completed = (
                client.table("study_participation")
                .select("status")
                .eq("study_subject_id", links[0]["study_subject_id"])
                .eq("status", "complete")
                .order("round_number", desc=True)
                .limit(1)
                .execute()
                .data
            )
        if not completed:
            raise HTTPException(status_code=403, detail=str(exc)) from exc

        return {**participant, "study_status": "complete"}


    return {
        **participant,
        "study_status": participation.status,
    }
