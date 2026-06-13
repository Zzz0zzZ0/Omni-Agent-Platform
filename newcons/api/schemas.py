"""
API Schema 定义 — 请求/响应模型。
"""
from pydantic import BaseModel, Field
from typing import Optional


# ── Chat ─────────────────────────────────────────────────────────

class ChatRequest(BaseModel):
    query: str
    use_agent: bool = True
    model_type: str = "cloud"
    use_auto_alpha: bool = True
    alpha: float = 0.5
    use_emotion: bool = True
    k_param: int = 3
    temp_param: float = 0.1


class ChatResponse(BaseModel):
    answer: str
    thoughts: list[str] = []
    persona: list = []
    arm_idx: int = -1
    context_vec: list = []


# ── Feedback ─────────────────────────────────────────────────────

class RecommendationFeedback(BaseModel):
    arm_idx: int
    context_vec: list
    reward: float


# ── Tenant ───────────────────────────────────────────────────────

class TenantCreate(BaseModel):
    name: str
    domain_id: str = "game_ops"
    config: Optional[dict] = None


class TenantResponse(BaseModel):
    id: str
    name: str
    api_key: str
    domain_id: str
    is_active: bool
