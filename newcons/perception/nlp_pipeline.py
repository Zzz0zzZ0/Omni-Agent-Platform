"""
NLP 感知流水线 — Schema 由 DomainPlugin 注入。
保留 structured_output + regex fallback 双链路。
"""
import json
import re

from langchain_core.prompts import ChatPromptTemplate
from core.logger import log


def get_llm(model_type: str = "cloud", temp: float = 0.1):
    if model_type == "local":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="qwen3:8b", temperature=temp)
    else:
        from langchain_community.chat_models import ChatTongyi
        return ChatTongyi(model="qwen-plus", temperature=temp)


def analyze_user_query(query: str, perception_schema=None, system_prompt: str = "", model_type="cloud", temp_val=0.1):
    """
    统一感知接口。
    perception_schema: 由 DomainPlugin.get_perception_schema() 提供的 Pydantic 类。
    """
    if perception_schema is None:
        from domains.game_ops.schemas import GameUserPerception
        perception_schema = GameUserPerception

    if not system_prompt:
        from domains.game_ops.prompts import PERCEPTION_SYSTEM_PROMPT
        system_prompt = PERCEPTION_SYSTEM_PROMPT

    try:
        llm = get_llm(model_type, temp_val)
        structured_llm = llm.with_structured_output(perception_schema)

        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", "{query}"),
        ])

        chain = prompt | structured_llm

        try:
            result = chain.invoke({"query": query})
            all_entities = list(set(
                getattr(result, "entities", []) + getattr(result, "game_entities", [])
            ))
            entities_formatted = [(e, "ENTITY") for e in all_entities]
            emotion = getattr(result, "emotion", "neutral")
            persona = getattr(result, "player_persona", ["未知画像"])
            return emotion, entities_formatted, persona

        except Exception as structure_e:
            log.warning(f"结构化输出解析失败，尝试 regex fallback: {structure_e}")

            fallback_prompt = ChatPromptTemplate.from_messages([
                ("system", (
                    f"{system_prompt}\n"
                    "请必须返回严格的JSON格式字符串，包含以下字段：\n"
                    "- emotion (字符串: 'positive', 'neutral', 'negative')\n"
                    "- entities (字符串数组: 核心实体)\n"
                    "- player_persona (字符串数组: 玩家画像)\n"
                    "- game_entities (字符串数组: 游戏专有名词)"
                )),
                ("human", "{query}"),
            ])
            fallback_chain = fallback_prompt | llm
            raw_res = fallback_chain.invoke({"query": query}).content

            json_match = re.search(r"\{.*\}", raw_res, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                emotion = parsed.get("emotion", "neutral")
                entities = parsed.get("entities", [])
                game_entities = parsed.get("game_entities", [])
                persona = parsed.get("player_persona", ["未知画像"])
                all_entities = list(set(entities + game_entities))
                return emotion, [(e, "ENTITY") for e in all_entities], persona
            else:
                raise ValueError("Regex fallback also failed")

    except Exception as e:
        log.error(f"感知模块提取异常: {e}")
        return "neutral", [], ["未知画像"]
