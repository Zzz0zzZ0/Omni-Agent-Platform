"""
游戏运营领域插件 — DomainPlugin 的核心实现。
将崩铁运营场景的 Prompt、工具、Schema、角色定义封装为可插拔模块。
"""
from typing import Type
from pydantic import BaseModel
from langchain_core.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchResults

from domains.base import DomainPlugin
from domains.game_ops.prompts import AGENT_SYSTEM_PROMPT
from domains.game_ops.tools import (
    gacha_calculator,
    analyze_community_feedback,
    generate_pr_announcement,
)
from domains.game_ops.schemas import GameUserPerception


class GameOpsDomainPlugin(DomainPlugin):

    @property
    def domain_id(self) -> str:
        return "game_ops"

    @property
    def display_name(self) -> str:
        return "游戏运营智能体"

    def get_agent_system_prompt(self) -> str:
        return AGENT_SYSTEM_PROMPT

    def get_tools(self, **kwargs) -> list[BaseTool]:
        tools: list[BaseTool] = [
            DuckDuckGoSearchResults(
                max_results=3,
                description="查询外部实时信息、游戏版本攻略、官网新闻时使用。",
            ),
            gacha_calculator,
            analyze_community_feedback,
            generate_pr_announcement,
        ]

        # 如果有知识库上下文，注入本地检索工具
        local_tool = kwargs.get("local_knowledge_tool")
        if local_tool:
            tools.append(local_tool)

        return tools

    def get_perception_schema(self) -> Type[BaseModel]:
        return GameUserPerception

    def get_ticket_operators(self) -> list[str]:
        return [
            "Comm_Specialist",   # 商业化运营 (负责充值、道具反馈)
            "PR_Specialist",     # 公关舆情 (负责辱骂、黑产、排雷)
            "Content_Planner",   # 活动策划 (负责关卡、剧情、建议)
            "Tech_Support",      # 技术维护 (负责闪退、Bug、渲染错误)
        ]

    def get_tag_keywords(self) -> dict[int, list[str]]:
        return {
            0: ["充值", "钱", "金币", "payment"],
            1: ["bug", "死机", "报错", "error"],
            2: ["策划", "建议", "关卡", "难度"],
        }

    def get_sentiment_prompt(self, event_text: str, enriched_text: str, similarity_context: str) -> str:
        from domains.game_ops.prompts import SENTIMENT_ANALYSIS_TEMPLATE
        return SENTIMENT_ANALYSIS_TEMPLATE.format(
            similarity_context=similarity_context,
            raw_text=event_text,
            enriched_text=enriched_text,
        )

    def get_routing_prompt(self, event_text: str, sentiment_score: int, intent_summary: str, similar_found: bool) -> str:
        from domains.game_ops.prompts import ROUTING_TEMPLATE
        return ROUTING_TEMPLATE.format(
            sentiment_score=sentiment_score,
            intent_summary=intent_summary,
            similar_incident_found=similar_found,
            raw_text=event_text,
        )

    def get_dashboard_config(self) -> dict:
        return {
            "roles": [
                {"id": "Comm_Specialist", "label": "商业化运营", "color": "#34d399"},
                {"id": "PR_Specialist", "label": "公关舆情员", "color": "#fbbf24"},
                {"id": "Content_Planner", "label": "活动策划", "color": "#38bdf8"},
                {"id": "Tech_Support", "label": "技术维护", "color": "#a78bfa"},
            ]
        }
