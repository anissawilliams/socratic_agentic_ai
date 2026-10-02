from collections.abc import Sequence

from langchain_core.messages import BaseMessage, HumanMessage

from app.graph.evaluate.criteria import PHASE_EVALUATION_CRITERIA
from app.config import LLM_MODEL_EVALUATOR
from app.models.evaluation import ResponseEvaluation
from app.services.llm import complete_structured
from app.socratic.phases import SocraticPhase
from app.socratic.prompts.evaluator import EVALUATOR_PROMPT


def evaluate_response(
    *,
    messages: Sequence[BaseMessage],
    current_phase: SocraticPhase,
    last_student_message: str,
    session_goal: str,
    model: str | None = None,
) -> ResponseEvaluation:
    """Evaluate the learner response against the current phase criteria."""

    evaluation_context = (
        f"Current phase: {current_phase}\n\n"
        "Scenario-level learning objective:\n"
        f"{session_goal}\n\n"
        "Evaluation criteria:\n"
        f"{PHASE_EVALUATION_CRITERIA[current_phase]}\n\n"
        "Latest learner response:\n"
        f"{last_student_message}"
)


    return complete_structured(
        [
            *messages,
            HumanMessage(content=evaluation_context),
        ],
        schema=ResponseEvaluation,
        model=model or LLM_MODEL_EVALUATOR,
        system=EVALUATOR_PROMPT,
        run_name="evaluate_response",
        metadata={
            "current_phase": current_phase,
        },
    )