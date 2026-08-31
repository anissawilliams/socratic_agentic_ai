from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.prompts.aporia import APORIA_PROMPT


def generate_aporia_response(state: TutorState) -> AIMessage:
    """Run one Aporia turn on the shared LLM using the full transcript."""
    return complete(
        state["messages"],
        system=APORIA_PROMPT,
        run_name="aporia",
        metadata={"socratic_phase": "aporia"},
    )
