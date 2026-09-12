from langchain_core.messages import AIMessage

from app.graph.state import TutorState

# Placeholder, kept in code rather than in scenario content because it is not
# settled: see "Reflection" in STUDY_DESIGN_QUESTIONS.md. A tutor-delivered
# recap does the learner's thinking for them, duplicates what Dialectic already
# asks for, and asserts a revision that not every participant made. It stands
# only until the team decides what this stage is for.
PLACEHOLDER_REFLECTION = (
    "Good — you've moved from 'citations = quality' to something more nuanced: "
    "citations are a preliminary signal, not proof. That's the kind of revision "
    "this process is meant to produce."
)


def generate_reflection(state: TutorState) -> dict:
    """Deliver the closing reflection after Socratic tutoring."""
    return {
        "messages": [AIMessage(content=PLACEHOLDER_REFLECTION)],
        "pending_event": "reflection_generated",
    }
