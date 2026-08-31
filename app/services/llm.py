from collections.abc import Sequence
from functools import lru_cache

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.config import (
    LLM_MODEL,
    LLM_PROMPT_VERSION,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
)


@lru_cache(maxsize=1)
def get_chat_model() -> ChatOpenAI:
    """Shared ChatOpenAI client. Agents must not construct their own."""
    if not OPENAI_API_KEY:
        raise RuntimeError("OPENAI_API_KEY must be configured.")

    return ChatOpenAI(
        model=LLM_MODEL,
        api_key=OPENAI_API_KEY,
        temperature=LLM_TEMPERATURE,
    )


def llm_metadata() -> dict[str, str | float]:
    """Model settings to stamp on research events / traces."""
    return {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "prompt_version": LLM_PROMPT_VERSION,
    }


def complete(
    messages: Sequence[BaseMessage],
    *,
    system: str | None = None,
    run_name: str | None = None,
    metadata: dict | None = None,
) -> AIMessage:
    payload: list[BaseMessage] = list(messages)

    if system is not None:
        payload = [SystemMessage(content=system), *payload]

    config = {
        "metadata": {
            **llm_metadata(),
            **(metadata or {}),
        }
    }

    if run_name is not None:
        config["run_name"] = run_name

    return get_chat_model().invoke(payload, config=config)