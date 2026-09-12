from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import system_prompt
from app.socratic.prompts.dialectic import DIALECTIC_PROMPT


def generate_dialectic_response(state: TutorState) -> AIMessage:
    """Run one Dialectic turn, told which moves have already been made."""
    messages = state["messages"]

    return complete(
        messages,
        system=system_prompt(DIALECTIC_PROMPT, messages),
        run_name="dialectic",
        metadata={"socratic_phase": "dialectic"},
    )
