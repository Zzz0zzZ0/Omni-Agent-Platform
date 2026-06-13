"""
通用工单处理流水线 — LangGraph 编排。
Prompt 和 Schema 由 DomainPlugin 注入。
"""
from typing import TypedDict, Any

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_community.chat_models import ChatTongyi

from domains.base import DomainPlugin
from domains.game_ops.schemas import SentimentAnalysis, TicketRouting, FeedbackEvent
from algorithms.linucb import LinUCBRecommender
from engine.vector_store import EmbeddingProvider
from core.logger import log


class TicketState(TypedDict):
    event: FeedbackEvent
    domain: DomainPlugin
    linucb: LinUCBRecommender
    sentiment: SentimentAnalysis
    routing: TicketRouting
    vectorstore: Any
    alert_triggered: bool
    recommended_operator: str
    arm_idx: int
    context_vec: list


def _query_similar(query: str, vectorstore, k: int = 2) -> str:
    if vectorstore is None:
        return "向量数据库未加载，无法对比历史数据。"
    docs = vectorstore.similarity_search(query, k=k)
    if not docs:
        return "未发现相似历史工单。"
    return "\n".join([f"[相似案例 {i+1}]: {d.page_content[:150]}..." for i, d in enumerate(docs)])


def sentiment_analyzer_node(state: TicketState):
    event = state["event"]
    vs = state["vectorstore"]
    domain = state["domain"]

    similarity_context = _query_similar(event.get_enriched_text(), vs)

    llm = ChatTongyi(model="qwen-plus", temperature=0).with_structured_output(SentimentAnalysis)
    prompt = domain.get_sentiment_prompt(event.raw_text_content, event.get_enriched_text(), similarity_context)
    result = llm.invoke([
        SystemMessage(content="你必须输出结构化的情绪与意图报告。"),
        HumanMessage(content=prompt),
    ])
    return {"sentiment": result}


def tagger_router_node(state: TicketState):
    event = state["event"]
    sentiment = state["sentiment"]
    domain = state["domain"]

    llm = ChatTongyi(model="qwen-plus", temperature=0).with_structured_output(TicketRouting)
    prompt = domain.get_routing_prompt(
        event.raw_text_content,
        sentiment.sentiment_score,
        sentiment.intent_summary,
        sentiment.similar_incident_found,
    )
    result = llm.invoke([
        SystemMessage(content="你必须输出结构化的路由报告。"),
        HumanMessage(content=prompt),
    ])
    return {"routing": result}


def alert_executor_node(state: TicketState):
    routing = state["routing"]
    event = state["event"]

    if routing.is_crisis or routing.priority == "P0":
        log.warning(
            f"🚨 [CRITICAL ALERT] Event={event.event_id} "
            f"Priority={routing.priority} Action={routing.action_item}"
        )
        return {"alert_triggered": True}
    return {"alert_triggered": False}


def recommender_node(state: TicketState):
    event = state["event"]
    sentiment = state["sentiment"]
    routing = state["routing"]
    linucb = state["linucb"]

    embeddings = EmbeddingProvider.get()
    full_emb = embeddings.embed_query(event.get_enriched_text())
    context_vec = linucb.build_context(full_emb, sentiment.sentiment_score, routing.tags)
    operator, arm_idx, x_t = linucb.recommend(context_vec)

    log.info(f"[Recommender] Ticket {event.event_id} → {operator}")
    return {
        "recommended_operator": operator,
        "arm_idx": arm_idx,
        "context_vec": x_t,
    }


def build_ticket_pipeline():
    workflow = StateGraph(TicketState)
    workflow.add_node("sentiment_analyzer", sentiment_analyzer_node)
    workflow.add_node("tagger_router", tagger_router_node)
    workflow.add_node("alert_executor", alert_executor_node)
    workflow.add_node("recommender", recommender_node)

    workflow.add_edge(START, "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "tagger_router")
    workflow.add_edge("tagger_router", "alert_executor")
    workflow.add_edge("alert_executor", "recommender")
    workflow.add_edge("recommender", END)

    return workflow.compile()
