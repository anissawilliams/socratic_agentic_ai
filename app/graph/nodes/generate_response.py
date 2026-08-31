from langchain_core.messages import AIMessage

from app.socratic.prompts import PHASE_CONTENT
from app.graph.state import TutorState


def generate_response(state: TutorState) -> dict:
    """Generate the tutor response for the current Socratic phase."""
    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError("Cannot generate a response without an active Socratic phase.")

    lines = PHASE_CONTENT[current_phase]

    attempt_count = state["phase_attempt_count"]
    line = lines[min(attempt_count, len(lines) - 1)]

    return {
        "messages": [AIMessage(content=line)],
        "pending_event": "turn_completed",
    }