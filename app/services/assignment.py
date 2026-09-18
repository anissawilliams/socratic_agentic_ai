"""Fail-closed access to precomputed study assignments."""

from dataclasses import dataclass

from app.services.supabase import get_supabase_client


@dataclass(frozen=True)
class StudyParticipation:
    id: str
    round_number: int
    cohort_code: str
    transfer_type: str
    assigned_condition_code: str
    tutor_scenario_key: str
    status: str


def current_study_participation(participant_id: str) -> StudyParticipation:
    """Return the participant's next pre-enrolled round or refuse access."""
    response = get_supabase_client().rpc(
        "get_current_study_participation",
        {"p_participant_id": participant_id},
    ).execute()
    rows = response.data or []
    if isinstance(rows, dict):
        rows = [rows]
    if len(rows) != 1:
        raise ValueError("Participant has no active study participation")

    row = rows[0]
    return StudyParticipation(
        id=str(row["id"]),
        round_number=int(row["round_number"]),
        cohort_code=str(row["cohort_code"]),
        transfer_type=str(row["transfer_type"]),
        assigned_condition_code=str(row["assigned_condition_code"]),
        tutor_scenario_key=str(row["tutor_scenario_key"]),
        status=str(row["status"]),
    )
