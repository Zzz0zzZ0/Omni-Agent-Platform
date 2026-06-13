"""
游戏运营领域 — Pydantic 结构化输出 Schema。
从旧 agent/ticket_models.py 和 perception/nlp_pipeline.py 迁移合并。
"""
from pydantic import BaseModel, Field
from typing import List, Optional


# ── NLP 感知 Schema ──────────────────────────────────────────────

class GameUserPerception(BaseModel):
    """游戏运营场景的玩家感知结构"""
    emotion: str = Field(
        description="用户情绪状态，必须是以下之一：positive, neutral, negative。如果是吐槽、抱怨，选择 negative。"
    )
    entities: List[str] = Field(
        description="用户提到的核心实体，如角色名、游戏玩法等。"
    )
    player_persona: List[str] = Field(
        description="根据用户发言推断的玩家画像标签，如 [强度党], [剧情党], [萌新], [零氪], [重氪] 等。"
    )
    game_entities: List[str] = Field(
        description="提取玩家发言中提到的游戏专有名词、角色名、物品名等实体（如：'限定角色', '深渊副本', '游戏代币'）"
    )


# ── Ticket Pipeline Schema ──────────────────────────────────────

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


# ── 多模态数据模型 ───────────────────────────────────────────────

class OCRResult(BaseModel):
    """单张图片的 OCR 提取结果"""
    image_name: str
    uid: Optional[str] = None
    gacha_count: Optional[int] = None
    error_codes: List[str] = []
    raw_text: str = ""


class FeedbackEvent(BaseModel):
    """统一的反馈事件模型"""
    import uuid as _uuid
    from datetime import datetime as _dt

    event_id: str = Field(default_factory=lambda: str(__import__("uuid").uuid4()))
    timestamp: str = Field(default_factory=lambda: __import__("datetime").datetime.now().isoformat())
    raw_text_content: str = ""
    structured_content: str = ""
    ocr_results: List[OCRResult] = []

    def get_enriched_text(self) -> str:
        """生成用于向量化增强的文本"""
        metadata_str = ""
        uids = {r.uid for r in self.ocr_results if r.uid}
        error_codes = {ec for r in self.ocr_results for ec in r.error_codes}

        if uids:
            metadata_str += f" [UID: {', '.join(uids)}]"
        if error_codes:
            metadata_str += f" [ErrorCodes: {', '.join(error_codes)}]"

        return f"{metadata_str} {self.structured_content or self.raw_text_content}".strip()
