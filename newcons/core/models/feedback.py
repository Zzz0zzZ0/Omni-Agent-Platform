"""反馈日志 ORM 模型 — 替代旧 database.py 中的裸 SQL"""
from datetime import datetime
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base


class FeedbackLogModel(Base):
    __tablename__ = "feedback_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tenant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("tenants.id"), index=True
    )
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    player_query: Mapped[str] = mapped_column(Text, nullable=False)
    emotion: Mapped[str] = mapped_column(String(16), default="neutral")
    player_persona: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="pending_review")
