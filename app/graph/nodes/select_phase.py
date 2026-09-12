from app.graph.state import TutorState
from app.socratic.phases import SocraticPhase, SOCRATIC_PHASE_ORDER



# TODO: Restore phase selection when the LLM-based response evaluator/judge is implemented.
def select_phase(state: TutorState) -> dict:
    """
    Temporary stub.

    Phase selection will be restored when the LLM-based
    response evaluator/judge is implemented.
    """
    raise NotImplementedError(
        "Phase selection is temporarily disabled pending the LLM evaluator."
    )