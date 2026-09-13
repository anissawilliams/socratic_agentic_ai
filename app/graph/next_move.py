import json
from collections.abc import Sequence

from langchain_core.messages import BaseMessage

from app.models.routing import RouteDecision, RoutingRecord
from app.services.llm import complete_structured
from app.socratic.phases import SocraticPhase
from app.socratic.prompts.router import (
    NEXT_MOVE_ROUTER_PROMPT,
)
from app.models.evaluation import ResponseEvaluation

_ROUTING_HISTORY_LIMIT = 8


def _action_for_phase(
    *,
    next_phase: SocraticPhase,
    current_phase: SocraticPhase,
    phase_history: Sequence[SocraticPhase],
) -> str:
    if next_phase == current_phase:
        return "stay"

    if next_phase in phase_history:
        return "revisit"

    return "switch"


def _runtime_context(
    *,
    current_phase: SocraticPhase,
    phase_history: Sequence[SocraticPhase],
    routing_history: Sequence[RoutingRecord],
    last_student_message: str,
    response_evaluation: ResponseEvaluation | None,
) -> dict:
    return {
        "current_phase": current_phase.value,
        "phase_history": [
            phase.value
            for phase in phase_history
        ],
        "recent_routing_history": [
            record.model_dump(mode="json")
            for record in routing_history[
                -_ROUTING_HISTORY_LIMIT:
            ]
        ],
        "latest_learner_response": last_student_message,
        "evaluation_guidance": (
            {
                "session_unresolved_issue":
                    response_evaluation.session_unresolved_issue,
                "follow_up_target":
                    response_evaluation.follow_up_target,
                "avoid_repeating":
                    response_evaluation.avoid_repeating,
            }
            if response_evaluation
            else None
        ),
    }

def _invoke_router(
    *,
    messages: Sequence[BaseMessage],
    system: str,
    current_phase: SocraticPhase,
    routing_history_length: int,
    run_name: str,
    retry_number: int,
) -> RouteDecision:
    return complete_structured(
        messages,
        schema=RouteDecision,
        system=system,
        run_name=run_name,
        metadata={
            "current_phase": current_phase.value,
            "routing_history_length": routing_history_length,
            "routing_retry_number": retry_number,
        },
    )


def _normal_target(target: str) -> str:
    return " ".join(target.lower().split())


def _repeats_previous_move(
    proposed: RouteDecision,
    previous: RoutingRecord,
) -> bool:
    same_signature = (
        proposed.topic == previous.topic
        and proposed.move_type == previous.move_type
    )

    same_target = (
        _normal_target(proposed.target)
        == _normal_target(previous.target)
    )

    return same_signature or same_target


def _safe_recovery_decision(
    *,
    current_phase: SocraticPhase,
    phase_history: Sequence[SocraticPhase],
    previous: RoutingRecord,
    rejected: RouteDecision,
) -> RouteDecision:
    """Return a concrete non-Aporia move after two repeated routes."""

    next_phase = SocraticPhase.DIALECTIC

    if previous.move_type == "apply_case":
        move_type = "compare"
        target = (
            "Present two concrete contrasting cases grounded in the "
            "learner's current position and ask them to distinguish "
            "how their standard applies to each. Do not request "
            "another explanation of a reason already provided."
        )
    else:
        move_type = "apply_case"
        target = (
            "Present one concrete borderline case grounded in the "
            "learner's latest claim and ask them to apply their "
            "current position to it. Do not request another reason "
            "or another elaboration of an established point."
        )

    avoid_repeating = list(
        dict.fromkeys(
            [
                *rejected.avoid_repeating,
                previous.target,
                rejected.target,
            ]
        )
    )

    return RouteDecision(
        action=_action_for_phase(
            next_phase=next_phase,
            current_phase=current_phase,
            phase_history=phase_history,
        ),
        next_phase=next_phase,
        topic=rejected.topic,
        move_type=move_type,
        target=target,
        reasoning_summary=(
            "Deterministic recovery after two router proposals "
            "repeated the immediately preceding topic and move type."
        ),
        avoid_repeating=avoid_repeating,
    )


def choose_next_move(
    *,
    messages: Sequence[BaseMessage],
    current_phase: SocraticPhase,
    phase_history: Sequence[SocraticPhase],
    routing_history: Sequence[RoutingRecord],
    last_student_message: str,
    response_evaluation: ResponseEvaluation | None,
) -> RouteDecision:
    runtime_context = _runtime_context(
    current_phase=current_phase,
    phase_history=phase_history,
    routing_history=routing_history,
    last_student_message=last_student_message,
    response_evaluation=response_evaluation,
)

    base_system = (
        f"{NEXT_MOVE_ROUTER_PROMPT}\n\n"
        "Current runtime context:\n"
        f"{json.dumps(runtime_context, indent=2)}"
    )

    proposed = _invoke_router(
        messages=messages,
        system=base_system,
        current_phase=current_phase,
        routing_history_length=len(routing_history),
        run_name="choose_next_move",
        retry_number=0,
    )

    if not routing_history:
        return proposed

    previous = routing_history[-1]

    if not _repeats_previous_move(
        proposed,
        previous,
    ):
        return proposed

    rejection_context = {
        "rejected_proposal": proposed.model_dump(mode="json"),
        "previous_accepted_route": previous.model_dump(
            mode="json"
        ),
    }

    retry_system = (
        f"{base_system}\n\n"
        "ROUTE REJECTION:\n"
        "Your proposed route repeated the immediately preceding "
        "topic and move type. That would produce another version "
        "of the same learner task.\n\n"
        "Choose a genuinely different conversational operation. "
        "You may remain on the same topic only if move_type changes. "
        "Prefer examine_evidence, test_limit, apply_case, compare, "
        "synthesize, or scaffold when grounded in the dialogue. "
        "Do not disguise repetition by paraphrasing the target.\n\n"
        f"{json.dumps(rejection_context, indent=2)}"
    )

    retried = _invoke_router(
        messages=messages,
        system=retry_system,
        current_phase=current_phase,
        routing_history_length=len(routing_history),
        run_name="choose_next_move_retry",
        retry_number=1,
    )

    if not _repeats_previous_move(
        retried,
        previous,
    ):
        return retried.model_copy(
            update={
                "reasoning_summary": (
                    "Accepted after rejecting a repetitive initial "
                    f"route. {retried.reasoning_summary}"
                )
            }
        )

    return _safe_recovery_decision(
        current_phase=current_phase,
        phase_history=phase_history,
        previous=previous,
        rejected=retried,
    )