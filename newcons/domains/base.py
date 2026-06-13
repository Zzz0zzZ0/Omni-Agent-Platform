"""
领域插件抽象基类 — 所有业务定制点的唯一入口。
新的游戏运营客户只需实现此接口即可接入平台。
"""
from abc import ABC, abstractmethod
from typing import Type
from pydantic import BaseModel
from langchain_core.tools import BaseTool


class DomainPlugin(ABC):
    """B 端领域插件抽象基类"""

    @property
    @abstractmethod
    def domain_id(self) -> str:
        """唯一标识，如 'game_ops'"""

    @property
    @abstractmethod
    def display_name(self) -> str:
        """显示名称"""

    @abstractmethod
    def get_agent_system_prompt(self) -> str:
        """Agent 的系统 Prompt"""

    @abstractmethod
    def get_tools(self, **kwargs) -> list[BaseTool]:
        """该领域专属的 Agent 工具集。kwargs 可传入 vectorstore、bm25 等上下文。"""

    @abstractmethod
    def get_perception_schema(self) -> Type[BaseModel]:
        """NLP 感知层的结构化输出 Schema"""

    @abstractmethod
    def get_ticket_operators(self) -> list[str]:
        """LinUCB 运营角色列表 (arm 定义)"""

    @abstractmethod
    def get_tag_keywords(self) -> dict[int, list[str]]:
        """LinUCB 标签特征的关键词映射 {维度索引: [关键词列表]}"""

    def get_sentiment_prompt(self, event_text: str, enriched_text: str, similarity_context: str) -> str:
        """工单情绪审查 Prompt，可覆盖"""
        return (
            f"你是一个高级运营审查员。请分析以下用户反馈并对比历史数据。\n"
            f"历史相似案例参考：\n{similarity_context}\n\n"
            f"用户反馈原文：\n{event_text}\n"
            f"增强上下文：\n{enriched_text}\n\n"
            f"请提取情绪分数（0-5）、核心诉求，并判断是否为已知/相似事件。"
        )

    def get_routing_prompt(self, event_text: str, sentiment_score: int, intent_summary: str, similar_found: bool) -> str:
        """工单路由分配 Prompt，可覆盖"""
        return (
            f"你是一个标签与路由分拣员。请根据审查报告为以下反馈打标并判定优先级。\n\n"
            f"审查报告：\n情绪分数: {sentiment_score}\n核心意图: {intent_summary}\n"
            f"历史相似性: {similar_found}\n\n反馈原文：\n{event_text}"
        )

    def get_dashboard_config(self) -> dict:
        """可选：自定义看板配置"""
        return {}
