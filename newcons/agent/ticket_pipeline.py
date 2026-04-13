from typing import Annotated, TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_community.chat_models import ChatTongyi
from langchain_core.messages import SystemMessage, HumanMessage
from core.models import FeedbackEvent
from .ticket_models import SentimentAnalysis, TicketRouting
from .ticket_tools import TicketTools
from algorithms.linucb import ticket_recommender
from engine.vector_store import embeddings

# 1. 定义流水线状态
class TicketState(TypedDict):
    event: FeedbackEvent
    sentiment: SentimentAnalysis
    routing: TicketRouting
    vectorstore: Any  # 传递 Chroma 实例用于检索
    alert_triggered: bool
    recommended_operator: str
    arm_idx: int
    context_vec: list

# 2. 构建核心节点
def sentiment_analyzer_node(state: TicketState):
    """节点 1：情绪与意图审查"""
    event = state["event"]
    vs = state["vectorstore"]
    
    # 接入 RAG：检索历史相似问题
    similarity_context = TicketTools.query_similar_issues(event.get_enriched_text(), vs)
    
    llm = ChatTongyi(model="qwen-plus", temperature=0).with_structured_output(SentimentAnalysis)
    
    prompt = f"""
你是一个高级游戏运营运营审查员。请分析以下玩家反馈并对比历史数据。
历史相似案例参考：
{similarity_context}

玩家反馈原文：
{event.raw_text_content}
多模态增强上下文：
{event.get_enriched_text()}

请提取情绪分数（0-5）、核心诉求，并判断是否为已知/相似事件。
"""
    result = llm.invoke([SystemMessage(content="你必须输出结构化的情绪与意图报告。"), HumanMessage(content=prompt)])
    
    return {"sentiment": result}

def tagger_router_node(state: TicketState):
    """节点 2：标签与路由分配"""
    event = state["event"]
    sentiment = state["sentiment"]
    
    llm = ChatTongyi(model="qwen-plus", temperature=0).with_structured_output(TicketRouting)
    
    prompt = f"""
你是一个标签与路由分拣员。请根据审查员的报告为以下玩家反馈打标并判定优先级。

审查员报告：
情绪分数: {sentiment.sentiment_score}
核心意图: {sentiment.intent_summary}
历史相似性: {sentiment.similar_incident_found}

反馈原文：
{event.raw_text_content}

规则：
1. 涉及充值、无法登录、或情绪 > 4 的评价，优先级提升为 P0 或 P1。
2. 如果是高危公关舆情（如辱骂开发者、威胁卸载、集体维权），标记 is_crisis 为 True。
"""
    result = llm.invoke([SystemMessage(content="你必须输出结构化的路由报告。"), HumanMessage(content=prompt)])
    
    return {"routing": result}

def alert_executor_node(state: TicketState):
    """节点 3：警报执行器 (条件触发)"""
    routing = state["routing"]
    event = state["event"]
    
    if routing.is_crisis or routing.priority == "P0":
        TicketTools.trigger_alert(
            priority=routing.priority,
            reason=f"Crisis detected: {routing.action_item}",
            event_id=event.event_id
        )
        return {"alert_triggered": True}
    
    return {"alert_triggered": False}

def recommender_node(state: TicketState):
    """节点 4：个性化推荐分发 (LinUCB)"""
    event = state["event"]
    sentiment = state["sentiment"]
    routing = state["routing"]
    
    # 获取文本 Embedding
    # 注意：在生产中建议缓存此 Embedding 或直接从 ingestion 传递过来
    full_emb = embeddings.embed_query(event.get_enriched_text())
    
    # 构造上下文向量
    context_vec = ticket_recommender.build_context(
        full_emb, 
        sentiment.sentiment_score, 
        routing.tags
    )
    
    operator, arm_idx, x_t = ticket_recommender.recommend(context_vec)
    
    print(f"[Recommender] Ticket {event.event_id} recommended to: {operator}")
    
    return {
        "recommended_operator": operator,
        "arm_idx": arm_idx,
        "context_vec": x_t
    }

# 3. 编排工作流
def build_ticket_pipeline():
    workflow = StateGraph(TicketState)
    
    # 添加节点
    workflow.add_node("sentiment_analyzer", sentiment_analyzer_node)
    workflow.add_node("tagger_router", tagger_router_node)
    workflow.add_node("alert_executor", alert_executor_node)
    workflow.add_node("recommender", recommender_node)
    
    # 构建边
    workflow.add_edge(START, "sentiment_analyzer")
    workflow.add_edge("sentiment_analyzer", "tagger_router")
    workflow.add_edge("tagger_router", "alert_executor")
    workflow.add_edge("alert_executor", "recommender")
    workflow.add_edge("recommender", END)
    
    return workflow.compile()

# 单例导出
app_ticket_pipeline = build_ticket_pipeline()
