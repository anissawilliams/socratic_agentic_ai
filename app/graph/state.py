from typing import Annotated, TypedDict
from enum import Enum
from langgraph.graph.message import add_messages
from app.socratic.phases import SocraticPhase
from app.models.evaluation import ResponseEvaluation
from app.persistence.events import EventType


class TutorCondition(str, Enum):
    SOCRATIC = "socratic"   # Default
    SCAFFOLDED = "scaffolded"
    DIRECT_CHAT = "direct_chat"

class TutorState(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]
    tutor_condition: TutorCondition | None
    current_phase: SocraticPhase | None
    previous_phase: SocraticPhase | None
    pending_event: EventType | None
    phase_attempt_count: int
    last_student_message: str
    response_evaluation: ResponseEvaluation | None
    next_action: str | None
    is_complete: bool
    completed_at: str | None