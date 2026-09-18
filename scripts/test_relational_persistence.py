"""Unit checks for typed tutor persistence without a live database."""

from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage

from app.content.scenarios import Scenario
from app.graph.state import TutorCondition
from app.models.evaluation import ResponseEvaluation
from app.models.routing import RouteDecision, RoutingRecord
from app.persistence import sessions
from app.socratic.phases import SocraticPhase


@dataclass
class FakeResponse:
    data: object


class FakeQuery:
    def __init__(self, rows):
        self.rows = rows

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self.rows = [row for row in self.rows if row.get(field) == value]
        return self

    def in_(self, *args):
        return self

    def limit(self, *args):
        return self

    def order(self, *args):
        return self

    def execute(self):
        return FakeResponse(self.rows)


class FakeRpc:
    def __init__(self, client, name, params):
        self.client = client
        self.name = name
        self.params = params

    def execute(self):
        self.client.calls.append((self.name, self.params))
        if self.name == "resolve_study_subject":
            return FakeResponse("subject-1")
        return FakeResponse(None)


class FakeClient:
    def __init__(self, tables=None):
        self.tables = tables or {}
        self.calls = []

    def rpc(self, name, params):
        return FakeRpc(self, name, params)

    def table(self, name):
        return FakeQuery(self.tables.get(name, []))


def evaluation() -> ResponseEvaluation:
    return ResponseEvaluation(
        phase_goal_satisfied=False,
        decision="stay",
        reasoning_summary="Reason",
        evidence="Evidence",
        learner_contribution="Contribution",
        addressed_question="Addressed",
        unresolved_issue="Issue",
        follow_up_target="Target",
        avoid_repeating=["Already answered"],
        session_goal_satisfied=False,
        session_unresolved_issue="Still unresolved",
        session_completion_reason=None,
    )


def route() -> RouteDecision:
    return RouteDecision(
        action="stay",
        next_phase=SocraticPhase.ELENCHUS,
        topic="citation_quality",
        move_type="probe_reason",
        target="The learner's quality criterion",
        reasoning_summary="Probe the stated reason",
        avoid_repeating=["Citation count definition"],
    )


def initial_state():
    return {
        "session_id": "00000000-0000-0000-0000-000000000001",
        "participant_id": "00000000-0000-0000-0000-000000000002",
        "study_participation_id": "00000000-0000-0000-0000-000000000020",
        "messages": [AIMessage(content="Opening question")],
        "tutor_condition": TutorCondition.SOCRATIC,
        "current_turn_id": "00000000-0000-0000-0000-000000000003",
        "current_phase": SocraticPhase.ELENCHUS,
        "previous_phase": None,
        "phase_history": [SocraticPhase.ELENCHUS],
        "route_decision": None,
        "routing_history": [],
        "pending_event": None,
        "last_student_message": "",
        "response_evaluation": None,
        "is_complete": False,
        "completed_at": None,
    }


def test_create_session_uses_typed_rpc():
    client = FakeClient()
    original = sessions.get_supabase_client
    sessions.get_supabase_client = lambda: client
    try:
        state = initial_state()
        scenario = Scenario(
            key="scenario-a",
            version="1.0.0",
            title="Scenario A",
            opening_question="Opening question",
            learning_objective="Objective",
            sha256="a" * 64,
        )
        sessions.create_session(
            state,
            assigned_condition_code="socratic_questioning",
            scenario=scenario,
        )
    finally:
        sessions.get_supabase_client = original

    name, params = client.calls[0]
    assert name == "start_tutor_session"
    assert params["p_assigned_condition_code"] == "socratic_questioning"
    assert params["p_runtime_condition_code"] == "socratic"
    assert all(not isinstance(value, dict) for value in params.values())


def test_save_turn_flattens_models():
    client = FakeClient()
    original = sessions.get_supabase_client
    sessions.get_supabase_client = lambda: client
    try:
        state = initial_state()
        state.update(
            {
                "current_turn_id": "00000000-0000-0000-0000-000000000004",
                "messages": [
                    AIMessage(content="Opening question"),
                    HumanMessage(content="Student answer"),
                    AIMessage(content="Tutor reply"),
                ],
                "last_student_message": "Student answer",
                "response_evaluation": evaluation(),
                "route_decision": route(),
                "routing_history": [
                    RoutingRecord(
                        phase=SocraticPhase.ELENCHUS,
                        topic="citation_quality",
                        move_type="probe_reason",
                        target="The learner's quality criterion",
                    )
                ],
            },
        )
        sessions.save_turn(
            state,
            phase_before=SocraticPhase.ELENCHUS,
            latency_ms=1250,
            input_tokens=321,
            output_tokens=87,
        )
    finally:
        sessions.get_supabase_client = original

    name, params = client.calls[0]
    assert name == "record_tutor_turn"
    assert params["p_participant_id"] == state["participant_id"]
    assert params["p_routing_topic_code"] == "citation_quality"
    assert params["p_evaluation_avoid_repeating"] == ["Already answered"]
    assert all(not isinstance(value, dict) for value in params.values())


def test_start_and_fail_turn_use_terminal_lifecycle_rpcs():
    client = FakeClient()
    original = sessions.get_supabase_client
    sessions.get_supabase_client = lambda: client
    try:
        state = initial_state()
        state["last_student_message"] = "Student answer"
        sessions.start_turn(state, phase_before=SocraticPhase.ELENCHUS)
        sessions.fail_turn(
            state,
            RuntimeError("provider unavailable"),
            latency_ms=30000,
            input_tokens=123,
            output_tokens=0,
        )
    finally:
        sessions.get_supabase_client = original

    assert [name for name, _ in client.calls] == [
        "start_tutor_turn",
        "fail_tutor_turn",
    ]
    start_params = client.calls[0][1]
    assert len(start_params["p_tutor_prompt_bundle_sha256"]) == 64
    assert len(start_params["p_prompt_sha256"]) == 64
    assert start_params["p_student_message"] == "Student answer"
    fail_params = client.calls[1][1]
    assert fail_params["p_error_code"] == "RuntimeError"


def test_load_session_reconstructs_state():
    session_id = "00000000-0000-0000-0000-000000000001"
    turn_id = "00000000-0000-0000-0000-000000000004"
    tables = {
        "tutor_session": [
            {
                "id": session_id,
                "study_subject_id": "subject-1",
                "study_participation_id": "participation-1",
                "runtime_condition_code": "socratic",
                "opening_turn_id": "00000000-0000-0000-0000-000000000003",
                "opening_message": "Opening question",
                "current_phase_code": "elenchus",
                "previous_phase_code": None,
                "status": "active",
                "completed_at": None,
            }
        ],
        "tutor_turn": [
            {
                "id": turn_id,
                "tutor_session_id": session_id,
                "status": "completed",
                "turn_number": 1,
                "student_message": "Student answer",
                "tutor_response": "Tutor reply",
                "phase_before_code": "elenchus",
                "phase_after_code": "elenchus",
                "previous_phase_code": None,
                "is_session_complete": False,
            },
            {
                "id": "00000000-0000-0000-0000-000000000099",
                "tutor_session_id": session_id,
                "status": "failed",
                "turn_number": 2,
                "student_message": "Failed answer",
                "tutor_response": None,
            },
        ],
        "response_evaluation": [
            {
                "tutor_turn_id": turn_id,
                "phase_goal_satisfied": False,
                "decision_code": "stay",
                "reasoning_summary": "Reason",
                "evidence": "Evidence",
                "learner_contribution": "Contribution",
                "addressed_question": "Addressed",
                "unresolved_issue": "Issue",
                "follow_up_target": "Target",
                "session_goal_satisfied": False,
                "session_unresolved_issue": "Still unresolved",
                "session_completion_reason": None,
            }
        ],
        "evaluation_avoid_repeating": [
            {
                "tutor_turn_id": turn_id,
                "item_order": 1,
                "content": "Already answered",
            }
        ],
        "routing_decision": [
            {
                "tutor_turn_id": turn_id,
                "action_code": "stay",
                "selected_phase_code": "elenchus",
                "topic_code": "citation_quality",
                "move_type_code": "probe_reason",
                "target": "The learner's quality criterion",
                "reasoning_summary": "Probe the stated reason",
            }
        ],
        "routing_avoid_repeating": [
            {
                "tutor_turn_id": turn_id,
                "item_order": 1,
                "content": "Citation count definition",
            }
        ],
    }
    client = FakeClient(tables)
    original = sessions.get_supabase_client
    sessions.get_supabase_client = lambda: client
    try:
        state = sessions.load_session(session_id, "participant-1")
    finally:
        sessions.get_supabase_client = original

    assert state is not None
    assert [message.content for message in state["messages"]] == [
        "Opening question",
        "Student answer",
        "Tutor reply",
    ]
    assert state["routing_history"][0].topic == "citation_quality"
    assert state["response_evaluation"].avoid_repeating == ["Already answered"]
    assert state["route_decision"].avoid_repeating == [
        "Citation count definition"
    ]


if __name__ == "__main__":
    test_create_session_uses_typed_rpc()
    test_save_turn_flattens_models()
    test_start_and_fail_turn_use_terminal_lifecycle_rpcs()
    test_load_session_reconstructs_state()
    print("ok")
