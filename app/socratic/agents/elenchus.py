from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import system_prompt
from app.socratic.prompts.elenchus import ELENCHUS_PROMPT


def generate_elenchus_response(state: TutorState) -> AIMessage:
    """Run one Elenchus turn, told which moves have already been made."""
    messages = state["messages"]

    return complete(
        messages,
        system=system_prompt(ELENCHUS_PROMPT, messages),
        run_name="elenchus",
        metadata={"socratic_phase": "elenchus"},
    )
