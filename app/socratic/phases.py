from enum import Enum

class SocraticPhase(str, Enum):
    ELENCHUS = "elenchus"
    APORIA = "aporia"
    MAIEUTICS = "maieutics"
    DIALECTIC = "dialectic"

SOCRATIC_PHASE_ORDER = [
    SocraticPhase.ELENCHUS,
    SocraticPhase.APORIA,
    SocraticPhase.MAIEUTICS,
    SocraticPhase.DIALECTIC,
]