from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import system_prompt
from app.socratic.prompts.maieutics import MAIEUTICS_PROMPT


def generate_maieutics_response(state: TutorState) -> AIMessage:
    """Run one Maieutics turn, told which moves have already been made."""
    messages = state["messages"]

    return complete(
        messages,
        system=system_prompt(MAIEUTICS_PROMPT, messages),
        run_name="maieutics",
        metadata={"socratic_phase": "maieutics"},
    )
