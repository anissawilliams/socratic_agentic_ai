from typing import Literal
from pydantic import BaseModel, Field


EvaluationDecision = Literal[
    "stay",
    "advance",
    "complete",
]


class ResponseEvaluation(BaseModel):
    phase_goal_satisfied: bool = Field(
        description="Whether the pedagogical goal of the current phase has been satisfied."
    )

    decision: EvaluationDecision = Field(
        description="Whether the tutor should stay in the current phase, advance, or complete."
    )

    reasoning_summary: str = Field(
        description="Brief explanation of why this decision was made."
    )

    evidence: str = Field(
        description="Evidence from the learner's response or dialogue supporting the decision."
    )
