import os
from datetime import datetime
from typing import List, Optional
from langchain_chroma import Chroma
from core.models import FeedbackEvent

class TicketTools:
    """流水线专用的外部工具集"""
    
    @staticmethod
    def query_similar_issues(query: str, vectorstore: Chroma, k: int = 2) -> str:
        """检索向量数据库中的相似历史反馈"""
        if vectorstore is None:
            return "向量数据库未加载，无法对比历史数据。"
        
        docs = vectorstore.similarity_search(query, k=k)
        if not docs:
            return "未发现相似历史工单。"
        
        results = []
        for i, doc in enumerate(docs):
            results.append(f"[相似案例 {i+1}]: {doc.page_content[:150]}...")
            
        return "\n".join(results)

    @staticmethod
    def trigger_alert(priority: str, reason: str, event_id: str):
        """触发高级警报 (当前实现为文件日志与控制台输出)"""
        alert_msg = f"""
🚨 [CRITICAL ALERT] 🚨
Timestamp: {datetime.now().isoformat()}
Event ID: {event_id}
Priority: {priority}
Reason: {reason}
------------------------------------
请运营团队立即介入处理！
"""
        print(alert_msg)
        
        # 记录到日志文件
        log_file = "alerts.log"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(alert_msg + "\n")
        
        return True
