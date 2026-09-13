from langgraph.graph import END, START, StateGraph

from app.graph.nodes.choose_next_move import (
    choose_next_move_node,
)
from app.graph.nodes.generate_response import generate_response
from app.graph.nodes.log_event import log_event
from app.graph.nodes.select_phase import select_phase
from app.graph.state import TutorState


def build_graph():
    graph = StateGraph(TutorState)

    graph.add_node(
        "choose_next_move",
        choose_next_move_node,
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
        "log_turn",
        log_event,
    )

    graph.add_edge(
        START,
        "choose_next_move",
    )

    graph.add_edge(
        "choose_next_move",
        "select_phase",
    )

    graph.add_edge(
        "select_phase",
        "generate_response",
    )

    graph.add_edge(
        "generate_response",
        "log_turn",
    )

    graph.add_edge(
        "log_turn",
        END,
    )

    return graph.compile()


tutor_graph = build_graph()