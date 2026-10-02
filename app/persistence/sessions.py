"""Relational tutor-session persistence with no JSON research payloads."""

from datetime import datetime, timezone
import logging
import time

import httpx

from langchain_core.messages import AIMessage, HumanMessage

from app.config import LLM_MODEL, LLM_MODEL_EVALUATOR, LLM_MODEL_ROUTER
from app.content.scenarios import Scenario
from app.graph.state import TutorCondition, TutorState
from app.models.evaluation import ResponseEvaluation
from app.models.routing import RouteDecision, RoutingRecord
from app.services.supabase import get_supabase_client
from app.services.provenance import prompt_bundle_provenance
from app.socratic.context import PHASE_KEY
from app.socratic.phases import SocraticPhase


logger = logging.getLogger(__name__)

_CONNECT_ATTEMPTS = 3


def _execute(request):
    """Execute a Supabase request, retrying only if the connection never opened.

    A connect timeout/error means the request never reached the database, so
    retrying cannot apply a write twice. Anything else (read timeouts, API
    errors) is raised immediately because the write may already have landed.
    """
    for attempt in range(1, _CONNECT_ATTEMPTS + 1):
        try:
            return request.execute()
        except (httpx.ConnectTimeout, httpx.ConnectError) as exc:
            if attempt == _CONNECT_ATTEMPTS:
                raise
            logger.warning(
                "Supabase connection failed (%s); retrying %d/%d",
                type(exc).__name__,
                attempt,
                _CONNECT_ATTEMPTS - 1,
            )
            time.sleep(0.5 * attempt)


def _value(value):
    return getattr(value, "value", value)


def _rpc_scalar(data):
    if isinstance(data, list):
        if not data:
            return None
        first = data[0]
        if isinstance(first, dict) and len(first) == 1:
            return next(iter(first.values()))
        return first
    return data


def create_session(
    state: TutorState,
    *,
    assigned_condition_code: str,
    scenario: Scenario,
    prompt_sha256: str | None = None,
) -> None:
    """Persist a new session and its opening message atomically."""
    opening_message = str(state["messages"][0].content)
    provenance = prompt_bundle_provenance()
    _execute(get_supabase_client().rpc(
        "start_tutor_session",
        {
            "p_session_id": state["session_id"],
            "p_participant_id": state["participant_id"],
            "p_study_participation_id": state["study_participation_id"],
            "p_assigned_condition_code": assigned_condition_code,
            "p_runtime_condition_code": _value(state["tutor_condition"]),
            "p_scenario_key": scenario.key,
            "p_scenario_version": scenario.version,
            "p_scenario_sha256": scenario.sha256,
            "p_tutor_prompt_bundle_key": provenance.key,
            "p_tutor_prompt_bundle_version": provenance.version,
            "p_tutor_prompt_bundle_sha256": provenance.sha256,
            "p_prompt_sha256": prompt_sha256 or provenance.tutor_prompt_sha256,
            "p_application_revision": provenance.application_revision,
            "p_model_name": LLM_MODEL,
            "p_opening_turn_id": state["current_turn_id"],
            "p_opening_message": opening_message,
            "p_current_phase_code": _value(state["current_phase"]),
        },
    ))


def start_turn(
    state: TutorState,
    *,
    phase_before: SocraticPhase | None,
    prompt_sha256: str | None = None,
) -> None:
    """Create the durable started row before invoking any model."""
    provenance = prompt_bundle_provenance()
    _execute(get_supabase_client().rpc(
        "start_tutor_turn",
        {
            "p_turn_id": state["current_turn_id"],
            "p_session_id": state["session_id"],
            "p_participant_id": state["participant_id"],
            "p_student_message": state["last_student_message"],
            "p_phase_before_code": _value(phase_before),
            "p_model_name": LLM_MODEL,
            "p_tutor_prompt_bundle_key": provenance.key,
            "p_tutor_prompt_bundle_version": provenance.version,
            "p_tutor_prompt_bundle_sha256": provenance.sha256,
            "p_prompt_sha256": prompt_sha256 or provenance.tutor_prompt_sha256,
            "p_application_revision": provenance.application_revision,
        },
    ))


def save_turn(
    state: TutorState,
    *,
    phase_before: SocraticPhase,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    """Persist one completed graph invocation through a typed transaction."""
    evaluation = state.get("response_evaluation")
    if evaluation is None:
        raise ValueError("Cannot persist a turn without its evaluation")

    route = state.get("route_decision")
    provenance = prompt_bundle_provenance()
    tutor_response = str(state["messages"][-1].content)
    completed_at = state.get("completed_at") or datetime.now(
        timezone.utc
    ).isoformat()

    params = {
        "p_turn_id": state["current_turn_id"],
        "p_session_id": state["session_id"],
        "p_participant_id": state["participant_id"],
        "p_tutor_response": tutor_response,
        "p_phase_before_code": phase_before.value,
        "p_phase_after_code": _value(state.get("current_phase")),
        "p_previous_phase_code": _value(state.get("previous_phase")),
        "p_is_session_complete": state["is_complete"],
        "p_completed_at": completed_at,
        "p_latency_ms": latency_ms,
        "p_input_tokens": input_tokens,
        "p_output_tokens": output_tokens,
        "p_phase_goal_satisfied": evaluation.phase_goal_satisfied,
        "p_evaluation_decision_code": evaluation.decision,
        "p_evaluation_reasoning_summary": evaluation.reasoning_summary,
        "p_evaluation_evidence": evaluation.evidence,
        "p_learner_contribution": evaluation.learner_contribution,
        "p_addressed_question": evaluation.addressed_question,
        "p_unresolved_issue": evaluation.unresolved_issue,
        "p_follow_up_target": evaluation.follow_up_target,
        "p_evaluation_avoid_repeating": evaluation.avoid_repeating,
        "p_session_goal_satisfied": evaluation.session_goal_satisfied,
        "p_session_unresolved_issue": evaluation.session_unresolved_issue,
        "p_session_completion_reason": evaluation.session_completion_reason,
        "p_evaluator_model_name": LLM_MODEL_EVALUATOR,
        "p_evaluator_prompt_version": provenance.evaluator_prompt_version,
        "p_evaluator_prompt_sha256": provenance.evaluator_prompt_sha256,
        "p_evaluator_application_revision": provenance.application_revision,
        "p_routing_action_code": route.action if route else None,
        "p_selected_phase_code": _value(route.next_phase) if route else None,
        "p_routing_topic_code": route.topic if route else None,
        "p_routing_move_type_code": route.move_type if route else None,
        "p_routing_target": route.target if route else None,
        "p_routing_reasoning_summary": route.reasoning_summary if route else None,
        "p_routing_avoid_repeating": route.avoid_repeating if route else [],
        "p_router_model_name": LLM_MODEL_ROUTER if route else None,
        "p_router_prompt_version": (
            provenance.router_prompt_version if route else None
        ),
        "p_router_prompt_sha256": (
            provenance.router_prompt_sha256 if route else None
        ),
        "p_router_application_revision": (
            provenance.application_revision if route else None
        ),
    }
    _execute(get_supabase_client().rpc("record_tutor_turn", params))


def save_direct_chat_turn(
    state: TutorState,
    *,
    tutor_response: str,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    """Record a control-condition turn: same turn row, no evaluation or routing."""
    _execute(get_supabase_client().rpc(
        "record_direct_chat_turn",
        {
            "p_turn_id": state["current_turn_id"],
            "p_session_id": state["session_id"],
            "p_participant_id": state["participant_id"],
            "p_tutor_response": tutor_response,
            "p_completed_at": datetime.now(timezone.utc).isoformat(),
            "p_latency_ms": latency_ms,
            "p_input_tokens": input_tokens,
            "p_output_tokens": output_tokens,
        },
    ))


def fail_turn(
    state: TutorState,
    error: Exception,
    *,
    latency_ms: int,
    input_tokens: int | None,
    output_tokens: int | None,
) -> None:
    """Terminally mark a started turn failed without exposing a traceback."""
    _execute(get_supabase_client().rpc(
        "fail_tutor_turn",
        {
            "p_turn_id": state["current_turn_id"],
            "p_session_id": state["session_id"],
            "p_participant_id": state["participant_id"],
            "p_error_code": type(error).__name__,
            "p_error_detail": str(error)[:2000],
            "p_latency_ms": latency_ms,
            "p_input_tokens": input_tokens,
            "p_output_tokens": output_tokens,
        },
    ))


def _rows_by_turn(rows: list[dict]) -> dict[str, dict]:
    return {str(row["tutor_turn_id"]): row for row in rows}


def _items_by_turn(rows: list[dict]) -> dict[str, list[str]]:
    grouped: dict[str, list[tuple[int, str]]] = {}
    for row in rows:
        grouped.setdefault(str(row["tutor_turn_id"]), []).append(
            (int(row["item_order"]), str(row["content"]))
        )
    return {
        turn_id: [content for _, content in sorted(items)]
        for turn_id, items in grouped.items()
    }


def load_session(
    session_id: str,
    participant_id: str,
) -> TutorState | None:
    """Reconstruct graph state from explicit relational rows."""
    client = get_supabase_client()
    subject_id = _rpc_scalar(
        _execute(client.rpc(
            "resolve_study_subject",
            {"p_participant_id": participant_id},
        )).data
    )
    if not subject_id:
        return None

    session_rows = (
        _execute(client.table("tutor_session")
        .select("*")
        .eq("id", session_id)
        .eq("study_subject_id", str(subject_id))
        .limit(1)
        )
        .data
        or []
    )
    if not session_rows:
        return None
    session = session_rows[0]

    turns = (
        _execute(client.table("tutor_turn")
        .select("*")
        .eq("tutor_session_id", session_id)
        .eq("status", "completed")
        .order("turn_number")
        )
        .data
        or []
    )
    turn_ids = [str(turn["id"]) for turn in turns]

    evaluations: dict[str, dict] = {}
    routes: dict[str, dict] = {}
    evaluation_avoid: dict[str, list[str]] = {}
    routing_avoid: dict[str, list[str]] = {}
    if turn_ids:
        evaluations = _rows_by_turn(
            _execute(client.table("response_evaluation")
            .select("*")
            .in_("tutor_turn_id", turn_ids)
            )
            .data
            or []
        )
        routes = _rows_by_turn(
            _execute(client.table("routing_decision")
            .select("*")
            .in_("tutor_turn_id", turn_ids)
            )
            .data
            or []
        )
        evaluation_avoid = _items_by_turn(
            _execute(client.table("evaluation_avoid_repeating")
            .select("tutor_turn_id,item_order,content")
            .in_("tutor_turn_id", turn_ids)
            )
            .data
            or []
        )
        routing_avoid = _items_by_turn(
            _execute(client.table("routing_avoid_repeating")
            .select("tutor_turn_id,item_order,content")
            .in_("tutor_turn_id", turn_ids)
            )
            .data
            or []
        )

    messages = [AIMessage(content=session["opening_message"])]
    routing_history: list[RoutingRecord] = []
    phase_history: list[SocraticPhase] = []
    if turns:
        first_phase = turns[0].get("phase_before_code")
        if first_phase:
            phase_history.append(SocraticPhase(first_phase))
    elif session.get("current_phase_code"):
        phase_history.append(SocraticPhase(session["current_phase_code"]))

    for turn in turns:
        turn_id = str(turn["id"])
        messages.append(HumanMessage(content=turn["student_message"]))
        kwargs = {}
        if turn.get("phase_after_code") and not turn["is_session_complete"]:
            kwargs[PHASE_KEY] = turn["phase_after_code"]
        messages.append(
            AIMessage(
                content=turn["tutor_response"],
                additional_kwargs=kwargs,
            )
        )

        route = routes.get(turn_id)
        if route:
            selected_phase = SocraticPhase(route["selected_phase_code"])
            routing_history.append(
                RoutingRecord(
                    phase=selected_phase,
                    topic=route["topic_code"],
                    move_type=route["move_type_code"],
                    target=route["target"],
                )
            )
            if not phase_history or selected_phase != phase_history[-1]:
                phase_history.append(selected_phase)

    last_turn = turns[-1] if turns else None
    last_turn_id = str(last_turn["id"]) if last_turn else None
    evaluation_row = evaluations.get(last_turn_id or "")
    route_row = routes.get(last_turn_id or "")

    evaluation = None
    if evaluation_row:
        evaluation = ResponseEvaluation(
            phase_goal_satisfied=evaluation_row["phase_goal_satisfied"],
            decision=evaluation_row["decision_code"],
            reasoning_summary=evaluation_row["reasoning_summary"],
            evidence=evaluation_row["evidence"],
            learner_contribution=evaluation_row["learner_contribution"],
            addressed_question=evaluation_row["addressed_question"],
            unresolved_issue=evaluation_row.get("unresolved_issue"),
            follow_up_target=evaluation_row.get("follow_up_target"),
            avoid_repeating=evaluation_avoid.get(last_turn_id or "", []),
            session_goal_satisfied=evaluation_row["session_goal_satisfied"],
            session_unresolved_issue=evaluation_row.get(
                "session_unresolved_issue"
            ),
            session_completion_reason=evaluation_row.get(
                "session_completion_reason"
            ),
        )

    route_decision = None
    if route_row:
        route_decision = RouteDecision(
            action=route_row["action_code"],
            next_phase=SocraticPhase(route_row["selected_phase_code"]),
            topic=route_row["topic_code"],
            move_type=route_row["move_type_code"],
            target=route_row["target"],
            reasoning_summary=route_row["reasoning_summary"],
            avoid_repeating=routing_avoid.get(last_turn_id or "", []),
        )

    current_phase = session.get("current_phase_code")
    previous_phase = session.get("previous_phase_code")
    return {
        "session_id": str(session["id"]),
        "participant_id": participant_id,
        "study_participation_id": str(session["study_participation_id"]),
        "messages": messages,
        "tutor_condition": TutorCondition(session["runtime_condition_code"]),
        "current_turn_id": last_turn_id or str(session["opening_turn_id"]),
        "current_phase": SocraticPhase(current_phase) if current_phase else None,
        "previous_phase": SocraticPhase(previous_phase) if previous_phase else None,
        "phase_history": phase_history,
        "route_decision": route_decision,
        "routing_history": routing_history,
        "pending_event": None,
        "last_student_message": last_turn["student_message"] if last_turn else "",
        "response_evaluation": evaluation,
        "is_complete": session["status"] == "complete",
        "completed_at": session.get("completed_at"),
    }
