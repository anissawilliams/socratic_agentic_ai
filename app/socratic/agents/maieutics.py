from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import maieutics_system_prompt


def generate_maieutics_response(state: TutorState) -> AIMessage:
    """Run one router-directed Maieutics turn."""

    messages = state["messages"]
    route_decision = state["route_decision"]

    if route_decision is None:
        raise ValueError(
            "Maieutics requires a routing decision."
        )

    return complete(
        messages,
        system=maieutics_system_prompt(
            messages,
            last_student_message=state["last_student_message"],
            route_decision=route_decision,
            evaluation=state["response_evaluation"],
        ),
        run_name="maieutics",
        metadata={
            "socratic_phase": "maieutics",
            "routing_action": route_decision.action,
            "routing_target": route_decision.target,
        },
    )