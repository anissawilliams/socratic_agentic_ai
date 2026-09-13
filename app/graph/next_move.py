from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage

from app.models.evaluation import ResponseEvaluation
from app.models.routing import RouteDecision
from app.services.llm import complete_structured
from app.socratic.phases import SocraticPhase
from app.socratic.prompts.router import NEXT_MOVE_ROUTER_PROMPT


def choose_next_move(
    *,
    messages: Sequence[BaseMessage],
    current_phase: SocraticPhase,
    phase_history: Sequence[SocraticPhase],
    evaluation: ResponseEvaluation,
) -> RouteDecision:
    """Select the Socratic role that should generate the next response."""

    history_text = ", ".join(phase.value for phase in phase_history)

    routing_context = (
        f"Current phase: {current_phase.value}\n\n"
        f"Phase history: {history_text}\n\n"
        "Response evaluation:\n"
        f"{evaluation.model_dump_json(indent=2)}"
    )

    return complete_structured(
        [
            *messages,
            HumanMessage(content=routing_context),
        ],
        schema=RouteDecision,
        system=NEXT_MOVE_ROUTER_PROMPT,
        run_name="choose_next_move",
        metadata={
            "current_phase": current_phase.value,
            "phase_history": [
                phase.value for phase in phase_history
            ],
        },
    )