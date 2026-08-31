from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.prompts.dialectic import DIALECTIC_PROMPT


def generate_dialectic_response(state: TutorState) -> AIMessage:
    """Run one Dialectic turn on the shared LLM using the full transcript."""
    return complete(
        state["messages"],
        system=DIALECTIC_PROMPT,
        run_name="dialectic",
        metadata={"socratic_phase": "dialectic"},
    )
