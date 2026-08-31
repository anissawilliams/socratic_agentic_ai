from app.socratic.phases import SocraticPhase
from app.socratic.prompts.aporia import APORIA_PROMPT
from app.socratic.prompts.dialectic import DIALECTIC_PROMPT
from app.socratic.prompts.elenchus import ELENCHUS_PROMPT
from app.socratic.prompts.maieutics import MAIEUTICS_PROMPT

PHASE_CONTENT = {
    SocraticPhase.ELENCHUS: [
        "One of the main metrics that shows an academic paper is important and high-quality is the number of citations. What do you think — is that a fair claim?",
        "I notice you're assuming citation count is valid on its own. But what if a paper is cited for criticism, not praise? How would you respond to that?",
        "Let's slow down — what specifically makes you confident citations reflect quality, rather than just visibility?",
    ],
    SocraticPhase.APORIA: [
        "Here's a wrinkle: a widely cited paper may promote ideas that are ultimately misleading or incorrect. What do you think about that contradiction?",
    ],
    SocraticPhase.MAIEUTICS: [
        "Think of citations like a compass that sometimes points the wrong way. How might that affect your judgment of widely cited papers?",
    ],
    SocraticPhase.DIALECTIC: [
        "Given that replication and scrutiny build credibility, how would you encourage other students to evaluate a paper's quality?",
        "Let's get concrete — if you were reviewing a paper right now, what's the first thing you'd check besides its citation count?",
        "What would make you personally trust a paper, regardless of how many times it's been cited?",
    ],
}

REFLECTION_CONTENT = [
    "Good — you've moved from 'citations = quality' to something more nuanced: citations are a preliminary signal, not proof. That's the kind of revision this process is meant to produce.",
    "Let's recap: you're now looking for more than just citation count — you're considering the paper's content, its authors' reputation, and its context. That's a more nuanced approach to evaluation.",
    "You've moved beyond the initial assumption that citations alone determine quality. That's the kind of critical thinking we're aiming for here.",
]

__all__ = [
    "APORIA_PROMPT",
    "DIALECTIC_PROMPT",
    "ELENCHUS_PROMPT",
    "MAIEUTICS_PROMPT",
    "PHASE_CONTENT",
    "REFLECTION_CONTENT",
]
