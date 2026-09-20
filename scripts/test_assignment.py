"""Unit checks for fail-closed study participation resolution."""

from dataclasses import dataclass

from app.services import assignment


@dataclass
class FakeResponse:
    data: object


class FakeRpc:
    def __init__(self, data):
        self.data = data

    def execute(self):
        return FakeResponse(self.data)


class FakeClient:
    def __init__(self, data):
        self.data = data

    def rpc(self, name, params):
        assert name == "get_current_study_participation"
        assert params["p_participant_id"] == "participant-1"
        return FakeRpc(self.data)


def test_resolves_precomputed_assignment():
    original = assignment.get_supabase_client
    assignment.get_supabase_client = lambda: FakeClient(
        [
            {
                "id": "participation-1",
                "round_number": 1,
                "cohort_code": "political_science",
                "transfer_type": "near",
                "assigned_condition_code": "socratic_questioning",
                "tutor_scenario_key": "citation_quality",
                "pretest_instrument_key": "test_near_transfer",
                "pretest_scenario_key": "test_citation_pre",
                "tutor_scenario_key": "citation_quality",
                "posttest_instrument_key": "test_near_transfer",
                "posttest_scenario_key": "test_citation_post",
                "status": "tutor",
            }
        ]
    )
    try:
        resolved = assignment.current_study_participation("participant-1")
    finally:
        assignment.get_supabase_client = original

    assert resolved.id == "participation-1"
    assert resolved.round_number == 1
    assert resolved.assigned_condition_code == "socratic_questioning"


def test_refuses_missing_assignment():
    original = assignment.get_supabase_client
    assignment.get_supabase_client = lambda: FakeClient([])
    try:
        try:
            assignment.current_study_participation("participant-1")
        except ValueError as exc:
            assert "no active study participation" in str(exc)
        else:
            raise AssertionError("missing assignment was accepted")
    finally:
        assignment.get_supabase_client = original


if __name__ == "__main__":
    test_resolves_precomputed_assignment()
    test_refuses_missing_assignment()
    print("ok")
