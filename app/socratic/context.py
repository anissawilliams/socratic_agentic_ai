"""Label tutor turns with the role that produced them.

The transcript alone does not say which role said what, so every agent used to
re-read the same flat history, independently pick the most salient move, and
land on the move a previous phase had already made. Labelling past turns is what
lets a role see that its move has already been spent.
"""

from collections.abc import Sequence

from langchain_core.messages import AIMessage, BaseMessage

from app.socratic.phases import SocraticPhase

PHASE_KEY = "socratic_phase"
OPENING_LABEL = "opening question"

# Long enough to identify the move that was made, short enough to keep the
# system prompt from competing with the transcript for attention.
_QUOTE_LIMIT = 240


def tag_phase(message: AIMessage, phase: SocraticPhase) -> AIMessage:
    """Record which role produced a tutor message."""
    message.additional_kwargs[PHASE_KEY] = phase.value
    return message


def phase_of(message: BaseMessage) -> str:
    """The role behind a tutor message, or the opening if it was scripted."""
    return message.additional_kwargs.get(PHASE_KEY, OPENING_LABEL)


def _quote(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= _QUOTE_LIMIT:
        return collapsed
    return f"{collapsed[:_QUOTE_LIMIT].rstrip()}…"


def phase_context(messages: Sequence[BaseMessage]) -> str:
    """Describe the tutor moves already made, for inclusion in a system prompt."""
    tutor_turns = [m for m in messages if isinstance(m, AIMessage)]

    if not tutor_turns:
        return (
            "No tutor move has been made yet. The learner is responding to the "
            "opening question."
        )

    lines = [
        f"  {index}. {phase_of(message)}: \"{_quote(str(message.content))}\""
        for index, message in enumerate(tutor_turns, start=1)
    ]

    spoken = sorted({phase_of(m) for m in tutor_turns} - {OPENING_LABEL})
    already = ", ".join(spoken) if spoken else "none yet"

    return (
        "Tutor moves already made in this dialogue:\n"
        + "\n".join(lines)
        + f"\n\nRoles that have already spoken: {already}.\n"
        "Do not repeat a move listed above. If the question you were about to "
        "ask has effectively been asked already, it is not your move to make — "
        "find the question that belongs to your role and has not been asked."
    )


def system_prompt(role_prompt: str, messages: Sequence[BaseMessage]) -> str:
    """Combine a role's standing instructions with what has happened so far."""
    return f"{role_prompt}\n\n{phase_context(messages)}"
