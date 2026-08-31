from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.socratic.prompts import REFLECTION_CONTENT


def generate_reflection(state: TutorState) -> dict:
    """Generate the closing reflection after Socratic tutoring."""
    reflection = REFLECTION_CONTENT[0]

    return {
        "messages": [AIMessage(content=reflection)],
        "pending_event": "reflection_generated",
    }