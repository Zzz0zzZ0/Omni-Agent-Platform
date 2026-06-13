"""
通用 Agent Graph — 工具与 Prompt 由 DomainPlugin 注入，不再硬编码业务逻辑。
"""
from typing import Annotated, TypedDict
from langchain_core.messages import SystemMessage, AnyMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tools import BaseTool

from core.logger import log


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]


def build_graph_agent(
    tools: list[BaseTool],
    system_prompt: str,
    model_type: str = "cloud",
    temp_param: float = 0.1,
    **kwargs,
):
    """构建通用 Agent Graph。tools 和 system_prompt 由 DomainPlugin 提供。"""
    if model_type == "local":
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="qwen3:8b", temperature=temp_param)
    else:
        from langchain_community.chat_models import ChatTongyi
        llm = ChatTongyi(model="qwen-plus", temperature=temp_param)

    llm_with_tools = llm.bind_tools(tools)
    sys_msg = SystemMessage(content=system_prompt)

    def call_model(state: AgentState):
        response = llm_with_tools.invoke([sys_msg] + state["messages"])
        return {"messages": [response]}

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_edge(START, "agent")
    workflow.add_conditional_edges("agent", tools_condition)
    workflow.add_edge("tools", "agent")

    return workflow.compile()
