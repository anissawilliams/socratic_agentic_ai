from app.graph.state import ResponseEvaluation
from app.graph.state import TutorState

HEDGE_WORDS = [
                "maybe", 
                "i guess", 
                "i don't know", 
                "not sure", 
                "i think so"]

def looks_like_hedging(answer: str) -> bool:
    lower = answer.lower()
    too_short = len(answer.strip().split()) < 5
    has_hedge = any(w in lower for w in HEDGE_WORDS)
    return too_short or has_hedge

def evaluate_student_response(state: TutorState) -> dict:
    hedging = looks_like_hedging(state["last_student_message"])

    evaluation = ResponseEvaluation(
        hedging_detected=hedging
    )

    return {"response_evaluation": evaluation}