from typing import Annotated, TypedDict
from langgraph.graph.message import add_messages


class TutorState(TypedDict):
    session_id: str
    messages: Annotated[list, add_messages]
    current_phase: str        # "elenchus" | "aporia" | "maieutics" | "dialectic" | "reflection_exit"
    attempt_count: int
    last_student_message: str
    hedging_detected: bool  # promoted from private field, now part of public contract
    next_action: str | None   # "stay" | "advance" — decide_next_step's raw output, nothing else touches this meaning
    is_complete: bool
    completed_at: str | None