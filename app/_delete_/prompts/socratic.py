PHASE_ORDER = ["elenchus", "aporia", "maieutics", "dialectic", "reflection_exit"]

PHASE_CONTENT = {
    "elenchus": [
        "One of the main metrics that shows an academic paper is important and high-quality is the number of citations. What do you think — is that a fair claim?",
        "I notice you're assuming citation count is valid on its own. But what if a paper is cited for criticism, not praise? How would you respond to that?",
        "Let's slow down — what specifically makes you confident citations reflect quality, rather than just visibility?",
    ],
    "aporia": [
        "Here's a wrinkle: a widely cited paper may promote ideas that are ultimately misleading or incorrect. What do you think about that contradiction?",

    ],
    "maieutics": [
        "Think of citations like a compass that sometimes points the wrong way. How might that affect your judgment of widely cited papers?",
           ],
   "dialectic": [
    "Given that replication and scrutiny build credibility, how would you encourage other students to evaluate a paper's quality?",
    "Let's get concrete — if you were reviewing a paper right now, what's the first thing you'd check besides its citation count?",
    "What would make you personally trust a paper, regardless of how many times it's been cited?",
],
    "reflection_exit": [
        "Good — you've moved from 'citations = quality' to something more nuanced: citations are a preliminary signal, not proof. That's the kind of revision this process is meant to produce.",
        "Let's recap: you're now looking for more than just citation count — you're considering the paper's content, its authors' reputation, and its context. That's a more nuanced approach to evaluation.",
        "You've moved beyond the initial assumption that citations alone determine quality. That's the kind of critical thinking we're aiming for here.",
    ],
}

ELENCHUS_PROMPT = """You are the Elenchus agent in a Socratic tutoring system.
Your job is to test the logical consistency of the student's claim through
cross-examination — not to state your own opinion or give the answer.

Use question types like:
- Probing assumptions ("What is being assumed here? Could the assumption be different?")
- Probing reasons and evidence ("How do you know that? What would count as evidence against it?")
- Viewpoints ("How might someone who disagrees see this?")
- Implications ("If that's true, what does it imply for X?")

Ask exactly one focused question per turn. Do not lecture. Do not summarize
what the student said back to them at length — engage it directly."""