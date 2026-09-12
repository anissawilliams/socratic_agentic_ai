from app.models.evaluation import ResponseEvaluation, ResponseType
from app.graph.state import TutorState

# Provisional heuristic. It decides which phase speaks and for how long, so it is
# effectively a research instrument and needs validating against human coding
# before conclusions rest on it — see STUDY_DESIGN_QUESTIONS.md.

HEDGE_PHRASES = (
    "maybe",
    "i guess",
    "i don't know",
    "i dont know",
    "dunno",
    "not sure",
    "i think so",
    "no idea",
    "hard to say",
)

# A message consisting of nothing but one of these is a decision, not an
# evasion. Conceding a point is what Aporia exists to produce, and it is
# usually said in one word.
ASSENT_PHRASES = frozenset(
    {
        "yes",
        "yeah",
        "yep",
        "yup",
        "ok",
        "okay",
        "sure",
        "agreed",
        "i agree",
        "true",
        "correct",
        "right",
        "that's right",
        "thats right",
        "fair",
        "fair enough",
        "no",
        "nope",
    }
)

REASON_MARKERS = (
    "because",
    "since",
    "due to",
    "so that",
    "therefore",
    "as a result",
)

MIN_SUBSTANTIVE_WORDS = 5


def _matched_hedge_phrase(lowered: str) -> str | None:
    return next(
        (phrase for phrase in HEDGE_PHRASES if phrase in lowered),
        None,
    )


def is_bare_assent(answer: str) -> bool:
    """True when the entire message is agreement or refusal and nothing else."""
    return answer.strip().strip(".!?,;:'\"").strip().lower() in ASSENT_PHRASES


def looks_like_hedging(answer: str) -> bool:
    """Whether the router should hold the learner in the current phase.

    Brevity still signals a non-answer, except when the brevity is the answer.
    A bare "yes" to "which of the two do you give up?" completes the phase; the
    previous version scored it as hedging and held the learner there for another
    attempt, at the exact moment the phase had succeeded.
    """
    lowered = answer.lower()
    too_short = len(answer.strip().split()) < MIN_SUBSTANTIVE_WORDS

    if _matched_hedge_phrase(lowered) is not None:
        return True

    return too_short and not is_bare_assent(answer)


def _classify(answer: str, *, uncertain: bool, reasoning: bool) -> ResponseType:
    if is_bare_assent(answer):
        return "minimal"

    if uncertain and not reasoning:
        return "unclear"

    if len(answer.strip().split()) < MIN_SUBSTANTIVE_WORDS:
        return "minimal"

    return "substantive"


def evaluate_student_response(state: TutorState) -> dict:
    answer = state["last_student_message"]
    lowered = answer.lower()

    hedge_phrase = _matched_hedge_phrase(lowered)
    reasoning = any(marker in lowered for marker in REASON_MARKERS)
    uncertain = hedge_phrase is not None

    evaluation = ResponseEvaluation(
        hedging_detected=looks_like_hedging(answer),
        response_type=_classify(answer, uncertain=uncertain, reasoning=reasoning),
        reasoning_present=reasoning,
        uncertainty_present=uncertain,
        word_count=len(answer.strip().split()),
        matched_hedge_phrase=hedge_phrase,
        bare_assent=is_bare_assent(answer),
    )

    return {
        "response_evaluation": evaluation,
    }
