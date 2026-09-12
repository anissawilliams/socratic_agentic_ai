from app.graph.state import TutorState
from app.socratic.context import tag_phase
from app.socratic.agents import (
    generate_aporia_response,
    generate_dialectic_response,
    generate_elenchus_response,
    generate_maieutics_response,
)
from app.socratic.phases import SocraticPhase


_AGENTS = {
    SocraticPhase.ELENCHUS: generate_elenchus_response,
    SocraticPhase.APORIA: generate_aporia_response,
    SocraticPhase.MAIEUTICS: generate_maieutics_response,
    SocraticPhase.DIALECTIC: generate_dialectic_response,
}


def generate_response(state: TutorState) -> dict:
    """Dispatch to the Socratic agent for the current phase."""
    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError("Cannot generate a response without an active Socratic phase.")

    agent = _AGENTS.get(current_phase)
    if agent is None:
        raise ValueError(f"No Socratic agent for phase: {current_phase}")

    # Tagging the turn is what lets later phases see which moves are spent.
    response = tag_phase(agent(state), current_phase)

    return {
        "messages": [response],
        "phase_turns_taken": state.get("phase_turns_taken", 0) + 1,
        "pending_event": "turn_completed",
    }
