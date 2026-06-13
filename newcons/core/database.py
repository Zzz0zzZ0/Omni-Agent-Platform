"""
数据库引擎 — SQLAlchemy async + aiosqlite
替代旧版裸 sqlite3 硬编码。
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from core.settings import settings
from core.models.base import Base
from core.logger import log

# 确保 data 目录存在
os.makedirs("data", exist_ok=True)

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False},  # SQLite 需要
)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def init_db() -> None:
    """创建所有表 (开发模式，生产建议迁移到 Alembic)"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    log.info("Database tables initialized")


async def get_db():
    """FastAPI 依赖：提供 async session 并自动 commit/rollback"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
