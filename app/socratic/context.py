"""Build role-specific context for Socratic tutor responses."""

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage
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
) -> str:
    """Describe the router-assigned move."""

    if route_decision is None:
        return (
            "No routing decision was supplied. Ask one focused "
            "question grounded in the learner's latest contribution."
        )

    lines = [
        "Assigned move:",
        f"- Selected role: {route_decision.next_phase.value}",
        f"- Topic: {route_decision.topic}",
        f"- Move type: {route_decision.move_type}",
        f"- Target: {route_decision.target}",
    ]

    if route_decision.avoid_repeating:
        lines.append("- Do not repeat:")
        lines.extend(
            f"  - {item}"
            for item in route_decision.avoid_repeating
        )

        lines.extend(
        [
            "",
            "Carry out the selected role only in service of the "
            "assigned target.",
            "Begin directly with the focused question or concrete "
            "case.",
            'Never begin with "You mentioned", "You highlighted", '
            '"You pointed out", "You noted", "It sounds like", '
            '"It seems", or an appraisal of the learner.',
            "Do not summarize the learner's preceding response "
            "before asking the question.",
            "Do not praise or evaluate the learner.",
            "Ask no more than one focused question.",
        ]
    )

    return "\n".join(lines)


def system_prompt(
    role_prompt: str,
    messages: Sequence[BaseMessage],
    *,
    route_decision: RouteDecision | None = None,
) -> str:
    """Combine role instructions, history, and assigned move."""

    return (
        f"{role_prompt}\n\n"
        f"{phase_context(messages)}\n\n"
        f"{assigned_move_context(route_decision)}"
    )

def maieutics_system_prompt(
    messages: Sequence[BaseMessage],
    *,
    last_student_message: str,
    route_decision: RouteDecision | None = None,
) -> str:
    """Build Maieutics instructions from the assigned move."""

    from app.socratic.prompts.maieutics import (
        MAIEUTICS_PROMPT,
    )

    latest = " ".join(last_student_message.split())

    base_prompt = system_prompt(
        MAIEUTICS_PROMPT,
        messages,
        route_decision=route_decision,
    )

    return (
        f"{base_prompt}\n\n"
        "Latest learner contribution:\n"
        f'  "{latest}"\n\n'
        "Develop the assigned target from what the learner is "
        "actually expressing. Do not infer agreement from brevity."
    )