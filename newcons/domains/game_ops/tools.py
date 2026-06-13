"""
游戏运营领域 — Agent 工具集。
从旧 agent/tools.py 迁移，保留游戏业务逻辑。
"""
import os
import sqlite3

from langchain_core.tools import tool
from langchain_community.chat_models import ChatTongyi

from domains.game_ops.prompts import PR_ANNOUNCEMENT_PROMPT


@tool
def gacha_calculator(current_pity: int, target_copies: int) -> str:
    """当用户询问抽卡规划、大保底计算时调用此工具"""
    cost_per_pull = 160
    expected_pulls_per_copy = 94
    total_expected_pulls = max(0, (target_copies * expected_pulls_per_copy) - current_pity)
    total_jade_needed = total_expected_pulls * cost_per_pull
    return (
        f"【运营数值推演】目标抽取 {target_copies} 只，当前水位 {current_pity} 抽。"
        f"预计还需 {total_expected_pulls} 抽，折合游戏代币约 {total_jade_needed}。"
    )


@tool
def analyze_community_feedback() -> str:
    """当运营人员要求总结今天的社区舆情、玩家负面反馈时调用此工具"""
    db_file = "./data/platform.db"
    if not os.path.exists(db_file):
        return "【舆情大盘】当前数据库为空。"
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM feedback_logs")
        total_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM feedback_logs WHERE emotion = 'negative'")
        neg_count = cursor.fetchone()[0]

        cursor.execute(
            "SELECT player_query, player_persona FROM feedback_logs "
            "WHERE emotion = 'negative' ORDER BY id DESC LIMIT 3"
        )
        recent_rows = cursor.fetchall()

        recent_complaints = "\n".join(
            [f"- {row[0]} (画像: {row[1]})" for row in recent_rows]
        )
        conn.close()
        return (
            f"【舆情大盘分析】目前共收录 {total_count} 条反馈，高危负面 {neg_count} 条。\n"
            f"近期核心槽点：\n{recent_complaints}"
        )
    except Exception as e:
        return f"读取舆情数据库失败: {str(e)}"


@tool
def generate_pr_announcement(issue_summary: str, compensation: str = "300游戏代币") -> str:
    """当运营人员要求撰写滑轨公告、道歉信时调用此工具。"""
    prompt = PR_ANNOUNCEMENT_PROMPT.format(
        issue_summary=issue_summary, compensation=compensation
    )
    llm = ChatTongyi(model="qwen-plus", temperature=0.7)
    res = llm.invoke(prompt)
    return f"【已自动生成公关滑轨草案，请审核】\n\n{res.content}"
