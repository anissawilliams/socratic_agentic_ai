from app.graph.state import TutorState
from app.socratic.agents import (
    generate_aporia_response,
    generate_dialectic_response,
    generate_elenchus_response,
    generate_maieutics_response,
)
from app.socratic.context import tag_phase
from app.socratic.phases import SocraticPhase


_AGENTS = {
    SocraticPhase.ELENCHUS: generate_elenchus_response,
    SocraticPhase.APORIA: generate_aporia_response,
    SocraticPhase.MAIEUTICS: generate_maieutics_response,
    SocraticPhase.DIALECTIC: generate_dialectic_response,
}


def generate_response(state: TutorState) -> dict:
    """Dispatch to the agent selected by the next-move router."""

    current_phase = state["current_phase"]
    route_decision = state["route_decision"]

    if current_phase is None:
        raise ValueError(
            "Cannot generate a response without an active Socratic phase."
        )

    if route_decision is None:
        raise ValueError(
            "Cannot generate a response without a routing decision."
        )

    if route_decision.next_phase != current_phase:
        raise ValueError(
            "Routing state is inconsistent: "
            f"router selected {route_decision.next_phase.value!r}, "
            f"but current phase is {current_phase.value!r}."
        )

    agent = _AGENTS.get(current_phase)

    if agent is None:
        raise ValueError(
            f"No Socratic agent is registered for phase "
            f"{current_phase.value!r}."
        )

    response = agent(state)

    # Preserve role provenance for repetition control, research logging,
    # and later fidelity evaluation.
    tagged_response = tag_phase(
        response,
        current_phase,
    )

    return {
        "messages": [tagged_response],
        "pending_event": "turn_completed",
    }