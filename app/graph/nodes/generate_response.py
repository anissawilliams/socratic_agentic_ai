from app.graph.state import TutorState
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

    return {
        "messages": [agent(state)],
        "pending_event": "turn_completed",
    }
