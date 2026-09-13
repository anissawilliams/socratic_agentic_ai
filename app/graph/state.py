from enum import Enum
from typing import Annotated, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from app.models.routing import RouteDecision, RoutingRecord
from app.persistence.events import EventType
from app.socratic.phases import SocraticPhase


class TutorCondition(str, Enum):
    SOCRATIC = "socratic"
    DIRECT_CHAT = "direct_chat"


class TutorState(TypedDict):
    session_id: str
    participant_id: str

    messages: Annotated[
        list[BaseMessage],
        add_messages,
    ]

    tutor_condition: TutorCondition | None

    current_phase: SocraticPhase | None
    previous_phase: SocraticPhase | None
    phase_history: list[SocraticPhase]

    route_decision: RouteDecision | None
    routing_history: list[RoutingRecord]

    pending_event: EventType | None
    current_turn_id: str | None
    last_student_message: str

    is_complete: bool
    completed_at: str | None