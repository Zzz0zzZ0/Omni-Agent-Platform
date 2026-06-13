"""租户 ORM 模型"""
import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column

from core.models.base import Base


class TenantModel(Base):
    __tablename__ = "tenants"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    api_key: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, index=True,
        default=lambda: f"hap_{uuid.uuid4().hex}"
    )
    domain_id: Mapped[str] = mapped_column(String(64), default="game_ops")
    config: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
