from typing import Literal, NotRequired, TypedDict

ResponseType = Literal[
    "substantive",
    "minimal",
    "unclear",
    "off_topic",
]

class ResponseEvaluation(TypedDict):
    # Temporary heuristic used by current prototype.
    hedging_detected: bool

    # Provisional richer evaluation fields.
    response_type: NotRequired[ResponseType]
    reasoning_present: NotRequired[bool]
    uncertainty_present: NotRequired[bool]
    phase_goal_satisfied: NotRequired[bool]
    reasoning_summary: NotRequired[str]