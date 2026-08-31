from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.prompts.elenchus import ELENCHUS_PROMPT


def generate_elenchus_response(state: TutorState) -> AIMessage:
    """Run one Elenchus turn on the shared LLM using the full transcript."""
    return complete(
        state["messages"],
        system=ELENCHUS_PROMPT,
        run_name="elenchus",
        metadata={"socratic_phase": "elenchus"},
    )
