from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.prompts.maieutics import MAIEUTICS_PROMPT


def generate_maieutics_response(state: TutorState) -> AIMessage:
    """Run one Maieutics turn on the shared LLM using the full transcript."""
    return complete(
        state["messages"],
        system=MAIEUTICS_PROMPT,
        run_name="maieutics",
        metadata={"socratic_phase": "maieutics"},
    )
