from langgraph.graph import StateGraph, START, END

from app.graph.state import TutorState
from app.graph.nodes.assess_response import assess_response
from app.graph.nodes.decide_next_step import decide_next_step
from app.graph.nodes.generate_response import generate_response
from app.graph.nodes.complete_session import complete_session

from app.graph.nodes.generate_elenchus import generate_elenchus
from app.graph.nodes.generate_maieutics import generate_maieutics
from app.graph.nodes.generate_dialectic import generate_dialectic
from app.graph.nodes.generate_reflection_exit import generate_reflection_exit
from app.graph.nodes.generate_aporia import generate_aporia

def route_to_phase_node(state: dict) -> str:
    if state["current_phase"] == "aporia":
        return "generate_aporia"
    elif state["current_phase"] == "elenchus":
        return "generate_elenchus"
    elif state["current_phase"] == "maieutics":
        return "generate_maieutics"
    elif state["current_phase"] == "dialectic":
        return "generate_dialectic"
    elif state["current_phase"] == "reflection_exit":
        return "generate_reflection_exit"
    else:
        return "complete_session"


def build_graph():
    graph = StateGraph(TutorState)

    graph.add_node("assess_response", assess_response)
    graph.add_node("decide_next_step", decide_next_step)
    #graph.add_node("generate_response", generate_response)
    graph.add_node("generate_aporia", generate_aporia)
    graph.add_node("generate_elenchus", generate_elenchus)
    graph.add_node("generate_maieutics", generate_maieutics)
    graph.add_node("generate_dialectic", generate_dialectic)
    graph.add_node("generate_reflection_exit", generate_reflection_exit)
    graph.add_node("complete_session", complete_session)

    graph.add_edge(START, "assess_response")
    graph.add_edge("assess_response", "decide_next_step")

    # decide_next_step routes to exactly one of the 5 phase generators — always
    graph.add_conditional_edges(
    "decide_next_step",
    route_to_phase_node,
    {
        "elenchus": "generate_elenchus",
        "aporia": "generate_aporia",
        "maieutics": "generate_maieutics",
        "dialectic": "generate_dialectic",
        "reflection_exit": "generate_reflection_exit",
    },
)

# four of the five just end the turn normally
    graph.add_edge("generate_elenchus", END)
    graph.add_edge("generate_aporia", END)
    graph.add_edge("generate_maieutics", END)
    graph.add_edge("generate_dialectic", END)

    # only reflection_exit's generate node leads to session cleanup
    graph.add_edge("generate_reflection_exit", "complete_session")
    graph.add_edge("complete_session", END)


    graph.add_edge("complete_session", END)

    return graph.compile()


tutor_graph = build_graph()