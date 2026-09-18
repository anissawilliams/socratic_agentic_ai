"""Verify turn-scoped aggregation of provider-reported token usage."""

from langchain_core.messages import AIMessage

from app.services.llm import _record_usage, collect_llm_usage


def test_aggregates_all_model_calls_in_turn():
    with collect_llm_usage() as usage:
        _record_usage(
            AIMessage(
                content="evaluation",
                usage_metadata={
                    "input_tokens": 100,
                    "output_tokens": 20,
                    "total_tokens": 120,
                },
            )
        )
        _record_usage(
            AIMessage(
                content="response",
                usage_metadata={
                    "input_tokens": 75,
                    "output_tokens": 30,
                    "total_tokens": 105,
                },
            )
        )

    assert usage.input_tokens == 175
    assert usage.output_tokens == 50


if __name__ == "__main__":
    test_aggregates_all_model_calls_in_turn()
    print("ok")
