"""Build role-specific context for Socratic tutor responses."""

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage

from app.models.evaluation import ResponseEvaluation
from app.models.routing import RouteDecision
from app.socratic.phases import SocraticPhase


PHASE_KEY = "socratic_phase"
OPENING_LABEL = "opening question"

_QUOTE_LIMIT = 200
_MOVE_HISTORY_LIMIT = 12


def tag_phase(message: AIMessage, phase: SocraticPhase) -> AIMessage:
    """Record which role produced a tutor message."""
    message.additional_kwargs[PHASE_KEY] = phase.value
    return message


def phase_of(message: BaseMessage) -> str:
    """Return the role behind a tutor message."""
    return message.additional_kwargs.get(PHASE_KEY, OPENING_LABEL)


def _quote(text: str) -> str:
    collapsed = " ".join(text.split())

    if len(collapsed) <= _QUOTE_LIMIT:
        return collapsed

    return f"{collapsed[:_QUOTE_LIMIT].rstrip()}…"


def phase_context(messages: Sequence[BaseMessage]) -> str:
    """Describe recent tutor moves so the next response does not repeat them."""

    tutor_turns = [
        message
        for message in messages
        if isinstance(message, AIMessage)
    ]

    if not tutor_turns:
        return (
            "No tutor move has been made yet. The learner is responding "
            "to the opening question."
        )

    recent_turns = tutor_turns[-_MOVE_HISTORY_LIMIT:]
    first_number = len(tutor_turns) - len(recent_turns) + 1

    lines = [
        (
            f'  {index}. {phase_of(message)}: '
            f'"{_quote(str(message.content))}"'
        )
        for index, message in enumerate(
            recent_turns,
            start=first_number,
        )
    ]

    return (
        "Recent tutor moves:\n"
        + "\n".join(lines)
        + "\n\nA Socratic role may be used more than once and may be "
        "revisited after another role. Reusing a role is appropriate only "
        "when it pursues a new, grounded target or meaningfully deepens the "
        "existing inquiry. Do not repeat a substantive question that the "
        "learner has already answered."
    )


def assigned_move_context(
    route_decision: RouteDecision | None,
    evaluation: ResponseEvaluation | None,
) -> str:
    """Describe the router-assigned move without exposing it as dialogue."""

    if route_decision is None:
        return (
            "No routing decision was supplied. Ask one focused question "
            "grounded in the learner's latest contribution."
        )

    lines = [
        "Assigned move:",
        f"- Selected role: {route_decision.next_phase.value}",
        f"- Target: {route_decision.target}",
    ]

    if evaluation is not None:
        if evaluation.unresolved_issue:
            lines.append(
                f"- Unresolved issue: {evaluation.unresolved_issue}"
            )

        if evaluation.follow_up_target:
            lines.append(
                f"- Evaluator follow-up target: "
                f"{evaluation.follow_up_target}"
            )

    avoid_repeating: list[str] = []

    if evaluation is not None:
        avoid_repeating.extend(evaluation.avoid_repeating)

    avoid_repeating.extend(route_decision.avoid_repeating)
    avoid_repeating = list(dict.fromkeys(avoid_repeating))

    if avoid_repeating:
        lines.append("- Do not repeat:")

        lines.extend(
            f"  - {item}"
            for item in avoid_repeating
        )

    lines.extend(
        [
            "",
            "Carry out the selected role only in service of the "
            "assigned target.",
            "Do not independently switch to a different issue merely "
            "because it seems more salient.",
            "Ask one focused question that moves the current inquiry "
            "forward.",
        ]
    )

    return "\n".join(lines)


def system_prompt(
    role_prompt: str,
    messages: Sequence[BaseMessage],
    *,
    route_decision: RouteDecision | None = None,
    evaluation: ResponseEvaluation | None = None,
) -> str:
    """Combine role instructions, dialogue history, and the assigned move."""

    return (
        f"{role_prompt}\n\n"
        f"{phase_context(messages)}\n\n"
        f"{assigned_move_context(route_decision, evaluation)}"
    )


def maieutics_system_prompt(
    messages: Sequence[BaseMessage],
    *,
    last_student_message: str,
    route_decision: RouteDecision | None = None,
    evaluation: ResponseEvaluation | None = None,
) -> str:
    """Build Maieutics instructions grounded in the latest contribution."""

    from app.socratic.prompts.maieutics import MAIEUTICS_PROMPT

    latest = " ".join(last_student_message.split())

    return (
        f"{system_prompt(
            MAIEUTICS_PROMPT,
            messages,
            route_decision=route_decision,
            evaluation=evaluation,
        )}\n\n"
        "Latest learner contribution:\n"
        f'  "{latest}"\n\n'
        "Develop the assigned target from what the learner is actually "
        "expressing. Do not infer agreement merely from brevity."
    )