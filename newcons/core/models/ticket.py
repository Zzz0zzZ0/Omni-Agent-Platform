"""工单 ORM 模型"""
import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Text, Integer, Float, Boolean, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base


class TicketModel(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), index=True
    )
    event_id: Mapped[str] = mapped_column(String(36), index=True)
    raw_text: Mapped[str] = mapped_column(Text, default="")
    enriched_text: Mapped[str] = mapped_column(Text, default="")

    # Sentiment
    sentiment_score: Mapped[int] = mapped_column(Integer, default=0)
    intent_summary: Mapped[str] = mapped_column(Text, default="")

    # Routing
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    priority: Mapped[str] = mapped_column(String(8), default="P3")
    is_crisis: Mapped[bool] = mapped_column(Boolean, default=False)
    action_item: Mapped[str] = mapped_column(Text, default="")

    # Recommendation
    recommended_operator: Mapped[str] = mapped_column(String(64), default="")
    arm_idx: Mapped[int] = mapped_column(Integer, default=-1)
    context_vec: Mapped[list | None] = mapped_column(JSON, nullable=True)

    # Status
    status: Mapped[str] = mapped_column(String(32), default="open")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
