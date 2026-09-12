from langchain_core.messages import AIMessage

from app.graph.state import TutorState
from app.services.llm import complete
from app.socratic.context import maieutics_system_prompt


def generate_maieutics_response(state: TutorState) -> AIMessage:
    """Run one Maieutics turn, extending the learner's latest thread."""
    messages = state["messages"]

    return complete(
        messages,
        system=maieutics_system_prompt(
            messages,
            last_student_message=state["last_student_message"],
        ),
        run_name="maieutics",
        metadata={"socratic_phase": "maieutics"},
    )
