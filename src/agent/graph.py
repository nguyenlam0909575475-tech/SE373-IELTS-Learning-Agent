"""Actual compiled LangGraph with a single bounded repair edge and filtered output."""

from typing import Callable

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import TypeAdapter

from .contracts import Dependencies, Identifier
from .nodes import MAX_ATTEMPTS, Nodes
from .state import AgentState, GraphInput, GraphOutput


def build_graph(
    *, dependencies: Dependencies
) -> CompiledStateGraph[AgentState, None, GraphInput, GraphOutput]:
    for version in (dependencies.model_version, dependencies.prompt_version):
        TypeAdapter(Identifier).validate_python(version)
    nodes = Nodes(dependencies)
    builder = StateGraph(AgentState, input_schema=GraphInput, output_schema=GraphOutput)
    for name in (
        "resolve_task",
        "prepare_tools",
        "retrieve_rubric",
        "examiner",
        "verify",
        "finalize",
        "failure",
    ):
        builder.add_node(name, nodes.wrap(name))
    builder.add_edge(START, "resolve_task")

    def guard(next_node: str) -> Callable[[AgentState], str]:
        def route(state: AgentState) -> str:
            return "failure" if state.get("error_code") else next_node

        return route

    for current, following in (
        ("resolve_task", "prepare_tools"),
        ("prepare_tools", "retrieve_rubric"),
        ("retrieve_rubric", "examiner"),
        ("examiner", "verify"),
    ):
        builder.add_conditional_edges(current, guard(following), [following, "failure"])

    def after_verify(state: AgentState) -> str:
        if state.get("error_code"):
            return "failure"
        if not state["validation_errors"]:
            return "finalize"
        return "examiner" if state["attempt_count"] < MAX_ATTEMPTS else "failure"

    builder.add_conditional_edges("verify", after_verify, ["finalize", "examiner", "failure"])
    builder.add_conditional_edges("finalize", guard(END), [END, "failure"])
    builder.add_edge("failure", END)
    return builder.compile()
