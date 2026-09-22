from collections.abc import Sequence
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from functools import lru_cache

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_openai import ChatOpenAI

from typing import TypeVar
from pydantic import BaseModel

from app.config import (
    LLM_MODEL,
    LLM_TEMPERATURE,
    OPENAI_API_KEY,
)
from app.services.provenance import prompt_bundle_provenance


@dataclass
class LLMUsage:
    input_tokens: int | None = None
    output_tokens: int | None = None


_usage_collector: ContextVar[LLMUsage | None] = ContextVar(
    "llm_usage_collector",
    default=None,
)


def _record_usage(message: AIMessage) -> None:
    collector = _usage_collector.get()
    usage = message.usage_metadata or {}
    if collector is not None and usage:
        collector.input_tokens = (collector.input_tokens or 0) + int(
            usage.get("input_tokens") or 0
        )
        collector.output_tokens = (collector.output_tokens or 0) + int(
            usage.get("output_tokens") or 0
        )


@contextmanager
def collect_llm_usage():
    """Aggregate provider-reported tokens for one synchronous tutor turn."""
    usage = LLMUsage()
    token = _usage_collector.set(usage)
    try:
        yield usage
    finally:
        _usage_collector.reset(token)


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
    provenance = prompt_bundle_provenance()
    return {
        "model": LLM_MODEL,
        "temperature": LLM_TEMPERATURE,
        "tutor_prompt_bundle_key": provenance.key,
        "tutor_prompt_bundle_version": provenance.version,
        "tutor_prompt_bundle_sha256": provenance.sha256,
        "tutor_prompt_sha256": provenance.tutor_prompt_sha256,
        "evaluator_prompt_sha256": provenance.evaluator_prompt_sha256,
        "router_prompt_sha256": provenance.router_prompt_sha256,
        "application_revision": provenance.application_revision,
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

    response = get_chat_model().invoke(payload, config=config)
    _record_usage(response)
    return response

StructuredOutput = TypeVar("StructuredOutput", bound=BaseModel)


def complete_structured(
    messages: Sequence[BaseMessage],
    *,
    schema: type[StructuredOutput],
    system: str | None = None,
    run_name: str | None = None,
    metadata: dict | None = None,
) -> StructuredOutput:
    """Invoke the shared chat model and return structured output."""

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

    model = get_chat_model().with_structured_output(schema, include_raw=True)
    result = model.invoke(payload, config=config)
    raw = result.get("raw")
    parsed = result.get("parsed")
    if isinstance(raw, AIMessage):
        _record_usage(raw)
    if parsed is None:
        error = result.get("parsing_error")
        raise ValueError("Structured model output could not be parsed") from error
    return parsed
