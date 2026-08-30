from langgraph.graph import StateGraph, START, END
from app.graph.state import TutorState
from app.graph.routing import route_after_phase_selection
from app.graph.nodes.evaluate import evaluate_student_response
from app.graph.nodes.select_phase import select_phase
from app.graph.nodes.generate_response import generate_response
from app.graph.nodes.generate_reflection import generate_reflection
from app.graph.nodes.complete_session import complete_session
from app.graph.nodes.log_turn import log_turn


def build_graph():
    graph = StateGraph(TutorState)

    graph.add_node(
        "log_turn",
        log_turn,
    )
    graph.add_node(
        "evaluate",
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

    graph.add_edge(
        START,
        "evaluate",
    )

    graph.add_edge(
        "evaluate",
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

    graph.add_edge(
    "generate_response",
    "log_turn",
    )

    graph.add_edge(
        "log_turn",
        END,
    )

    graph.add_edge(
        "generate_reflection",
        "complete_session",
    )

    graph.add_edge(
        "complete_session",
        END,
    )

    return graph.compile()


tutor_graph = build_graph()