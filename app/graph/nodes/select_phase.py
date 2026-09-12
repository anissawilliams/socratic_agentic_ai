from app.graph.state import TutorState
from app.socratic.phases import SocraticPhase, SOCRATIC_PHASE_ORDER


MAX_ATTEMPTS_PER_PHASE = 3

# A phase must generate at least this many tutor turns before the router may
# advance past it. The scripted opening question does not count: elenchus can
# only cross-examine a position the learner has already stated.


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