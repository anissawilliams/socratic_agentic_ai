from app.models.evaluation import ResponseEvaluation, ResponseType
from app.graph.state import TutorState




# TODO: Replace this with an LLM-based response evaluator/judge.
def evaluate_student_response(state: TutorState) -> dict:
    """
    Temporary stub.

    The previous deterministic response heuristics have been removed.
    This node will be replaced by the LLM-based response evaluator/judge.
    """
    return {
        "response_evaluation": None,
    }
