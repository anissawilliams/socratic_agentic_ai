from app.graph.evaluate.evaluator import evaluate_response
from app.graph.state import TutorState


def evaluate_student_response(state: TutorState) -> dict:
    current_phase = state["current_phase"]

    if current_phase is None:
        raise ValueError(
            "Cannot evaluate a student response without an active Socratic phase."
        )

    evaluation = evaluate_response(
        messages=state["messages"],
        current_phase=current_phase,
        last_student_message=state["last_student_message"],
    )

    return {"response_evaluation": evaluation}