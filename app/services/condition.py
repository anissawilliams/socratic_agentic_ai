"""Map persisted study condition codes to runtime tutor condition."""

from app.graph.state import TutorCondition

# Codes must match rows in public.study_condition (see sql/002_participant_condition.sql).
# Add new codes here before enrolling participants; unknown codes refuse session start.
_CONDITION_BY_CODE: dict[str, TutorCondition] = {
    "scenario_questioning": TutorCondition.SOCRATIC,
    "socratic": TutorCondition.SOCRATIC,
    "scaffolded": TutorCondition.SCAFFOLDED,
    "direct_chat": TutorCondition.DIRECT_CHAT,
}


def tutor_condition_for_participant(participant: dict) -> TutorCondition:
    """Resolve the participant's assigned condition for TutorState and logging."""
    raw = participant.get("condition")
    if raw is None or not str(raw).strip():
        raise ValueError("Participant has no assigned condition")

    code = str(raw).strip().lower()
    try:
        return _CONDITION_BY_CODE[code]
    except KeyError as exc:
        known = ", ".join(sorted(_CONDITION_BY_CODE))
        raise ValueError(
            f"Unknown condition code {code!r}; expected one of: {known}"
        ) from exc
