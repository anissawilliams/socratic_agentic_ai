"""The scenario both AI conditions discuss: the participant's pretest scenario.

The AI receives the scenario text the student already read, so it can refer
to the actual facts instead of guessing. It never receives the student's
pretest answers.
"""

from langchain_core.messages import BaseMessage, SystemMessage

from app.content.assessments import load_assessment_instrument


CONTEXT_MARKER = "scenario_context"


def scenario_context_message(pretest_instrument_key: str) -> tuple[SystemMessage, str]:
    """Return (context message, scenario title) for the pretest scenario."""
    content = load_assessment_instrument(pretest_instrument_key).pretest
    message = SystemMessage(
        content=(
            "Scenario under discussion. The student read this in the first "
            "part of the study. Use only these facts; do not invent numbers "
            "or details that are not given.\n\n"
            f"Title: {content.scenario_title}\n\n"
            f"{content.scenario_text}"
        ),
        additional_kwargs={CONTEXT_MARKER: True},
    )
    return message, content.scenario_title


def with_scenario_context(
    messages: list[BaseMessage], context: SystemMessage
) -> list[BaseMessage]:
    return [context, *without_scenario_context(messages)]


def without_scenario_context(messages: list[BaseMessage]) -> list[BaseMessage]:
    return [
        message
        for message in messages
        if not message.additional_kwargs.get(CONTEXT_MARKER)
    ]
