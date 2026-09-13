from app.graph.evaluate.evaluator import evaluate_response
from app.graph.state import TutorState
from app.content.scenarios import load_scenario


def evaluate_student_response(state: TutorState) -> dict:
    current_phase = state["current_phase"]
    scenario = load_scenario()
    session_goal = scenario.learning_objective

    if current_phase is None:
        raise ValueError(
            "Cannot evaluate a student response without an active Socratic phase."
        )

    evaluation = evaluate_response(
        messages=state["messages"],
        current_phase=current_phase,
        last_student_message=state["last_student_message"],
        session_goal=session_goal,
)

    return {"response_evaluation": evaluation}