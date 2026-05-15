from langgraph.graph import END, StateGraph

from app.agent.nodes import convert_to_images, format_response, query_model, validate_input
from app.agent.state import QAState


def _should_continue(state: QAState) -> str:
    return "abort" if state.get("error") else "continue"


def build_graph():
    builder = StateGraph(QAState)

    builder.add_node("validate", validate_input)
    builder.add_node("convert", convert_to_images)
    builder.add_node("query_model", query_model)
    builder.add_node("format", format_response)

    builder.set_entry_point("validate")

    builder.add_conditional_edges(
        "validate",
        _should_continue,
        {"continue": "convert", "abort": END},
    )
    builder.add_conditional_edges(
        "convert",
        _should_continue,
        {"continue": "query_model", "abort": END},
    )
    builder.add_conditional_edges(
        "query_model",
        _should_continue,
        {"continue": "format", "abort": END},
    )
    builder.add_edge("format", END)

    return builder.compile()


qa_graph = build_graph()
