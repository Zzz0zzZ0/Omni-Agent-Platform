from pydantic import BaseModel, Field
from typing import List, Optional

class SentimentAnalysis(BaseModel):
    """审核员的情绪与意图报告"""
    sentiment_score: int = Field(description="负面情绪等级，0（冷静）到 5（愤怒/失望）")
    intent_summary: str = Field(description="核心诉求摘要，例如：卡池机制报错")
    similar_incident_found: bool = Field(description="是否在历史库中发现相似事件")
    incident_details: Optional[str] = Field(default=None, description="相似事件的简要对比描述")

class TicketRouting(BaseModel):
    """标签与路由分配报告"""
    tags: List[str] = Field(description="业务标签列表，例：[bug], [payment], [balance]")
    priority: str = Field(description="优先级级别：P0 (紧急), P1, P2, P3")
    is_crisis: bool = Field(description="是否被判定为高危公关舆情/致命BUG")
    action_item: str = Field(description="建议的后续动作，例：通知开发组修复，或转人工客服")
