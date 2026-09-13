from typing import Literal
from pydantic import BaseModel, Field


EvaluationDecision = Literal[
    "stay",
    "advance",
]


class ResponseEvaluation(BaseModel):
    phase_goal_satisfied: bool = Field(
        description=(
            "Whether the learner has demonstrated the pedagogical goal "
            "of the current phase. This does not, by itself, require "
            "advancing or ending the discussion."
        )
    )

    decision: EvaluationDecision = Field(
        description=(
            "Whether to stay in the current phase for a productive "
            "follow-up or advance because a different pedagogical "
            "move is warranted. These are the only supported decisions."
        )
    )

    reasoning_summary: str = Field(
        description=(
            "Concise justification for the decision, grounded in "
            "observable dialogue content."
        )
    )

    evidence: str = Field(
        description=(
            "Specific statements from the dialogue supporting the "
            "assessment. Preserve the learner's qualifications and "
            "distinguish their statements from the tutor's suggestions."
        )
    )

    learner_contribution: str = Field(
        description=(
            "What the latest response adds, clarifies, challenges, or "
            "corrects, such as a claim, reason, evidence, qualification, "
            "or application. State when it adds nothing new."
        )
    )

    addressed_question: str = Field(
        description=(
            "Identify the preceding tutor question and explain whether "
            "the learner answered it fully, partly, or not at all. "
            "Recognize corrections of the tutor's interpretation."
        )
    )

    unresolved_issue: str | None = Field(
        description=(
            "One specific issue grounded in the dialogue that merits "
            "further exploration. Use null when none is supported. "
            "Do not manufacture a contradiction or missing evidence."
        )
    )

    follow_up_target: str | None = Field(
        description=(
            "The specific reasoning or evidence a useful next question "
            "would examine, rather than the wording of that question. "
            "Use null when no productive follow-up is identified."
        )
    )

    avoid_repeating: list[str] = Field(
        description=(
            "Questions or requests already adequately answered that "
            "the tutor should avoid repeating. Use an empty list "
            "when none are relevant."
        )
    )

    session_goal_satisfied: bool = Field(
    description=(
        "Whether the learner has demonstrated the scenario-level "
        "learning objective sufficiently that another substantive "
        "Socratic move is no longer warranted."
    )
)

    session_unresolved_issue: str | None = Field(
        description=(
            "One substantive issue that still prevents completion of the "
            "scenario-level learning objective. Use null when no such "
            "issue remains. Do not use optional detail, wording refinement, "
            "citation mechanics, or another possible example as a reason "
            "to continue."
        )
    )

    session_completion_reason: str | None = Field(
        description=(
            "When session_goal_satisfied is true, briefly explain what the "
            "learner has demonstrated across the dialogue that justifies "
            "ending the Socratic inquiry. Otherwise use null."
        )
    )