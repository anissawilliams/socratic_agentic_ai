"""Smoke tests for study condition → TutorCondition mapping."""

from app.graph.state import TutorCondition
from app.services.condition import tutor_condition_for_participant


def test_scenario_questioning_maps_to_socratic():
    assert (
        tutor_condition_for_participant(
            {"id": "1", "condition": "scenario_questioning"}
        )
        is TutorCondition.SOCRATIC
    )


def test_socratic_questioning_maps_to_socratic():
    assert (
        tutor_condition_for_participant(
            {"id": "1", "condition": "socratic_questioning"}
        )
        is TutorCondition.SOCRATIC
    )


def test_direct_chat():
    assert (
        tutor_condition_for_participant({"id": "1", "condition": "direct_chat"})
        is TutorCondition.DIRECT_CHAT
    )


def test_unknown_raises():
    try:
        tutor_condition_for_participant({"id": "1", "condition": "unknown_arm"})
    except ValueError as exc:
        assert "unknown_arm" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_scenario_questioning_maps_to_socratic()
    test_socratic_questioning_maps_to_socratic()
    test_direct_chat()
    test_unknown_raises()
    print("ok")
