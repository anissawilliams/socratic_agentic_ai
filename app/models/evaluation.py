from typing import Literal, NotRequired, TypedDict

ResponseType = Literal[
    "substantive",
    "minimal",
    "unclear",
    "off_topic",
]

class ResponseEvaluation(TypedDict):

    # The evaluation of the response.
    evaluation: str

