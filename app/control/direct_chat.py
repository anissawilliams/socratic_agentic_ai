"""Control condition: a standard, student-led AI assistant.

Same scenario, model, temperature, timer, and logging as the Socratic
condition. The only difference is the assistant's behavior: it answers,
explains, and advises directly, and the student decides where the
conversation goes.
"""

from hashlib import sha256

from langchain_core.messages import AIMessage, BaseMessage

from app.services.llm import complete


DIRECT_CHAT_PROMPT = """
You are a helpful AI assistant. A university student is working through the
scenario provided below as part of a study activity, and they will decide
what to ask you.

Respond the way a capable general-purpose AI assistant normally would:
answer their questions directly, explain your reasoning, analyze the
evidence, and give your own opinion or recommendation when they ask for it.
Help them understand the scenario and work toward the best answer.

Keep the conversation on this scenario and the questions it raises. If the
student asks about something unrelated, briefly and politely bring them back
to the scenario.

Use only the facts given in the scenario. If something is not stated, say
that it is not given rather than inventing it.

Write clearly and in plain language; many students are not native English
speakers. Keep responses reasonably concise.
""".strip()

DIRECT_CHAT_PROMPT_SHA256 = sha256(DIRECT_CHAT_PROMPT.encode("utf-8")).hexdigest()


# Wording approved by the research team.
CONTROL_OPENING = (
    "I'm here to help you work through the scenario you just considered. "
    "How can I help you?"
)


def opening_message(scenario_title: str) -> str:  # noqa: ARG001 (kept for callers)
    return CONTROL_OPENING


def respond(messages: list[BaseMessage]) -> AIMessage:
    """One assistant reply. `messages` already starts with the scenario context."""
    return complete(
        messages,
        system=DIRECT_CHAT_PROMPT,
        run_name="direct_chat",
        metadata={"tutor_condition": "direct_chat"},
    )
