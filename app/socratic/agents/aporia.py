from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import system_prompt
from app.socratic.prompts.aporia import APORIA_PROMPT


def generate_aporia_response(state: TutorState) -> AIMessage:
    """Run one Aporia turn, told which moves have already been made."""
    messages = state["messages"]

    return complete(
        messages,
        system=system_prompt(APORIA_PROMPT, messages),
        run_name="aporia",
        metadata={"socratic_phase": "aporia"},
    )
