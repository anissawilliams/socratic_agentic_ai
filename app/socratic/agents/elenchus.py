from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import system_prompt
from app.socratic.prompts.elenchus import ELENCHUS_PROMPT


def generate_elenchus_response(state: TutorState) -> AIMessage:
    """Run one router-directed Elenchus turn."""

    messages = state["messages"]
    route_decision = state["route_decision"]

    if route_decision is None:
        raise ValueError(
            "Elenchus requires a routing decision."
        )

    return complete(
        messages,
        system=system_prompt(
            ELENCHUS_PROMPT,
            messages,
            route_decision=route_decision,
        ),
        run_name="elenchus",
        metadata={
            "socratic_phase": route_decision.next_phase.value,
            "routing_action": route_decision.action,
            "routing_topic": route_decision.topic,
            "routing_move_type": route_decision.move_type,
            "routing_target": route_decision.target,
        },
    )