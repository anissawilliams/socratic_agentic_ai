from langchain_core.messages import AIMessage

from app.graph.state import TutorState

# NOT WIRED INTO THE GRAPH. Sessions now end after Dialectic with no closing
# tutor message; see app/graph/routing.py.
#
# This text is retained only as the record of what was removed and why. A
# tutor-delivered recap does the learner's thinking for them, duplicates what
# Dialectic already asks for, and asserts a revision that not every participant
# made — in a live run it congratulated a participant for abandoning a position
# she had rejected in her first reply. See "Reflection" in
# STUDY_DESIGN_QUESTIONS.md.
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
