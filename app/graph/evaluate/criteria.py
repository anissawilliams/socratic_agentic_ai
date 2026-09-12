from app.socratic.phases import SocraticPhase

# Provisional criteria pending team decisions on phase goals and progression.

PHASE_EVALUATION_CRITERIA: dict[SocraticPhase, str] = {
    "elenchus": (
        "The learner has articulated enough reasoning for the current "
        "cross-examination to have accomplished its purpose."
    ),
    "aporia": (
        "The learner meaningfully recognizes that the current account "
        "is inadequate, conflicted, or requires revision."
    ),
    "maieutics": (
        "The learner contributes a concrete element of a developing account "
        "that moves beyond the prior impasse."
    ),
    "dialectic": (
        "The learner has sufficiently developed and tested the emerging "
        "account to complete the interaction."
    ),
}