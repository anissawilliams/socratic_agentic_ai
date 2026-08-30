from langgraph.graph import StateGraph, START, END

from app.graph.state import TutorState
from app.graph.routing import route_after_phase_selection

from app.graph.nodes.evaluate_response import evaluate_student_response
from app.graph.nodes.select_phase import select_phase
from app.graph.nodes.generate_response import generate_response
from app.graph.nodes.generate_reflection import generate_reflection
from app.graph.nodes.complete_session import complete_session
from app.graph.nodes.log_event import log_event


def build_graph():
    graph = StateGraph(TutorState)

    graph.add_node(
        "evaluate_response",
        evaluate_student_response,
    )

    graph.add_node(
        "select_phase",
        select_phase,
    )

    graph.add_node(
        "generate_response",
        generate_response,
    )

    graph.add_node(
        "generate_reflection",
        generate_reflection,
    )

    graph.add_node(
        "complete_session",
        complete_session,
    )

    # Same logging implementation, invoked at different workflow points.
    graph.add_node(
        "log_turn",
        log_event,
    )

    graph.add_node(
        "log_reflection",
        log_event,
    )

    graph.add_node(
        "log_session_complete",
        log_event,
    )

    graph.add_edge(
        START,
        "evaluate_response",
    )

    graph.add_edge(
        "evaluate_response",
        "select_phase",
    )

    graph.add_conditional_edges(
        "select_phase",
        route_after_phase_selection,
        {
            "generate_response": "generate_response",
            "generate_reflection": "generate_reflection",
        },
    )

    # Normal Socratic turn
    graph.add_edge(
        "generate_response",
        "log_turn",
    )

    graph.add_edge(
        "log_turn",
        END,
    )

    # Reflection / session completion
    graph.add_edge(
        "generate_reflection",
        "log_reflection",
    )

    graph.add_edge(
        "log_reflection",
        "complete_session",
    )

    graph.add_edge(
        "complete_session",
        "log_session_complete",
    )

    graph.add_edge(
        "log_session_complete",
        END,
    )

    return graph.compile()


tutor_graph = build_graph()