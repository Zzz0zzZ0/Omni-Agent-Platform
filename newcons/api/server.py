from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
import tempfile
import os
import pandas as pd
import json  # 使用json替代ast
import sys
import threading  # 添加线程锁
from typing import List, Any
from langchain_community.chat_models import ChatTongyi
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.vector_store import build_hybrid_knowledge_base, visualize_semantic_space, add_feedback_event_to_db
from engine.rag_pipeline import get_answer_complex, log_negative_feedback_sync
from engine.ingestion_pipeline import IngestionPipeline
from agent.ticket_pipeline import app_ticket_pipeline
from core.models import FeedbackEvent
from algorithms.linucb import ticket_recommender
from agent.graph_brain import build_graph_agent
from langchain_community.retrievers import BM25Retriever


app = FastAPI(title="Cognitive Agent API", description="Game Intelligent Ops Dashboard Backend Engine")

# 启用 CORS 跨域支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # 生产环境建议指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加线程锁保护全局状态
global_memory = {
    "vectorstore": None,
    "bm25": None,
    "all_splits": [],
}
memory_lock = threading.Lock()

# 文件上传配置
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
ALLOWED_EXTENSIONS = {'.pdf', '.txt'}


class ChatRequest(BaseModel):
    query: str
    use_agent: bool = True
    model_type: str = "cloud"
    use_auto_alpha: bool = True
    alpha: float = 0.5
    use_emotion: bool = True
    # [新增] 恢复调节参数
    k_param: int = 3
    temp_param: float = 0.1

class FeedbackRequest(BaseModel):
    arm_idx: int
    context_vec: list
    reward: float


# 初始化全局管道实例 (延迟加载)
pipeline = IngestionPipeline()

async def run_ticket_pipeline_async(event: FeedbackEvent, vs: Any):
    """在后台不阻塞返回的情况下运行工单处理流"""
    try:
        inputs = {
            "event": event,
            "vectorstore": vs,
            "alert_triggered": False
        }
        # 使用 run_in_threadpool 因为 LangGraph 执行通常是同步且耗时的
        await run_in_threadpool(app_ticket_pipeline.invoke, inputs)
    except Exception as e:
        print(f"[Pipeline Error] Ticket pipeline failed: {e}")

@app.post("/api/v1/ingest/feedback")
async def ingest_feedback(
    background_tasks: BackgroundTasks,
    feedback_text: str = Form(None),
    doc_file: UploadFile = File(None),
    images: List[UploadFile] = File([])
):
    """
    接收图文混合反馈，利用 Docling 和 PaddleOCR 进行结构化解析并存入向量库
    """
    tmp_files = []
    try:
        # 1. 保存文档文件
        doc_path = None
        if doc_file:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(doc_file.filename)[1]) as tmp:
                tmp.write(await doc_file.read())
                doc_path = tmp.name
                tmp_files.append(doc_path)

        # 2. 保存图片文件
        img_paths = []
        for img_file in images:
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(img_file.filename)[1]) as tmp:
                tmp.write(await img_file.read())
                img_paths.append(tmp.name)
                tmp_files.append(tmp.name)

        # 3. 执行管道任务 (因为 OCR 比较慢，建议在 run_in_threadpool 中执行)
        event = await run_in_threadpool(
            pipeline.run, 
            text_content=feedback_text, 
            text_file_path=doc_path, 
            image_paths=img_paths
        )

        # 4. 存入向量库并触发工单流水线
        with memory_lock:
            vs = global_memory["vectorstore"]
            if vs:
                add_feedback_event_to_db(event, vs)
                # 将流水线处理丢入后台任务，不增加用户等待时长
                background_tasks.add_task(run_ticket_pipeline_async, event, vs)
            else:
                return {"status": "error", "message": "Vector store not initialized."}

        return {
            "status": "success",
            "event_id": event.event_id,
            "ocr_summary": [res.dict() for res in event.ocr_results],
            "enriched_text_preview": event.get_enriched_text()[:200]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 清理临时文件
        for f in tmp_files:
            if os.path.exists(f):
                os.remove(f)

@app.post("/upload_memory")
async def upload_memory(file: UploadFile = File(...)):
    """处理前端上传的文档，注入全局记忆并生成可视化数据"""
    try:
        # 验证文件扩展名
        file_ext = os.path.splitext(file.filename)[1].lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file type. Supported: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # 读取文件内容并验证大小
        file_content = await file.read()
        if len(file_content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"文件过大。最大允许 {MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # 基本内容验证（检查是否为空或全是空白字符）
        if not file_content or not file_content.strip():
            raise HTTPException(status_code=400, detail="文件内容为空")
        
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=file_ext
        ) as tmp_file:
            tmp_file.write(file_content)
            tmp_path = tmp_file.name

        vs, new_splits, count = build_hybrid_knowledge_base(tmp_path)
        
        # 使用线程锁保护全局状态更新
        with memory_lock:
            global_memory["vectorstore"] = vs
            global_memory["all_splits"].extend(new_splits)
            
            if global_memory["all_splits"]:
                global_bm25 = BM25Retriever.from_documents(global_memory["all_splits"])
                global_bm25.k = 10
                global_memory["bm25"] = global_bm25

        # 生成可视化 2D 坐标数据，并转换成 JSON 格式发给前端
        viz_df = visualize_semantic_space(vs)
        viz_data_json = viz_df.to_dict(orient="records") if viz_df is not None else []

        os.remove(tmp_path)
        return {
            "status": "success",
            "message": f"Memory solidified, {count} fragments processed.",
            "viz_data": viz_data_json,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat")
async def chat_endpoint(req: ChatRequest, background_tasks: BackgroundTasks):
    """处理所有的对话与 Agent 路由请求"""

    def clean_llm_output(raw_output):
        # 使用json.loads替代ast.literal_eval，更安全
        if isinstance(raw_output, str) and raw_output.strip().startswith("[{"):
            try:
                raw_output = json.loads(raw_output.strip())
            except json.JSONDecodeError:
                # 如果JSON解析失败，返回原始字符串
                pass

        # 应对列表结构提取纯文本
        if isinstance(raw_output, list):
            texts = [
                item.get("text", "")
                for item in raw_output
                if isinstance(item, dict) and "text" in item
            ]
            if texts:
                return "".join(texts)

        return str(raw_output)

    try:
        if req.use_agent:
            # 使用线程锁保护全局状态读取
            with memory_lock:
                vectorstore = global_memory["vectorstore"]
                bm25 = global_memory["bm25"]
            
            # 1. 启动 Agent 执行复杂工具流与多步推理
            agent_app = build_graph_agent(
                vectorstore,
                bm25,
                model_type=req.model_type,
                use_emotion=req.use_emotion,
                use_auto_alpha=req.use_auto_alpha,
                temp_param=req.temp_param,
                k_param=req.k_param,
            )
            response = await run_in_threadpool(agent_app.invoke, {"messages": [("user", req.query)]})

            # 清洗 Agent 输出的乱码
            raw_content = response["messages"][-1].content
            answer = clean_llm_output(raw_content)

            # 提取思考流
            thoughts = []
            for msg in response["messages"][1:-1]:
                if msg.type == "ai" and getattr(msg, "tool_calls", None):
                    for tc in msg.tool_calls:
                        thoughts.append(f"Tool Call: {tc['name']}")

            # 2. 旁路提取玩家画像标签与 LinUCB 特征
            persona_tags = []
            arm_idx = -1
            context_vec = []
            if req.use_emotion:
                try:
                    temp_result = await run_in_threadpool(
                        get_answer_complex,
                        vectorstore,
                        bm25,
                        req.query,
                        model_type=req.model_type,
                        alpha=req.alpha,
                        use_auto_alpha=req.use_auto_alpha,
                        use_emotion=True,
                        k_param=req.k_param,
                        temp_param=req.temp_param,
                    )
                    persona_tags = temp_result.get("persona", [])
                    arm_idx = temp_result.get("arm_idx", -1)
                    context_vec = temp_result.get("context_vec", [])
                    if temp_result.get("emotion") == "negative":
                       background_tasks.add_task(log_negative_feedback_sync, req.query, "negative", "|".join(persona_tags))
                except Exception as e:
                    print(f"旁路画像与权重特征提取失败: {e}")

            return {
                "answer": answer,
                "thoughts": thoughts,
                "persona": persona_tags,
                "arm_idx": arm_idx,
                "context_vec": context_vec,
            }

        else:
            # 使用线程锁保护全局状态读取
            with memory_lock:
                vectorstore = global_memory["vectorstore"]
                bm25 = global_memory["bm25"]
                
            result = await run_in_threadpool(
                get_answer_complex,
                vectorstore,
                bm25,
                req.query,
                model_type=req.model_type,
                alpha=req.alpha,
                use_auto_alpha=req.use_auto_alpha,
                use_emotion=req.use_emotion,
                k_param=req.k_param,
                temp_param=req.temp_param,
            )

            if result.get("emotion") == "negative":
                 persona_tags = result.get("persona", [])
                 background_tasks.add_task(log_negative_feedback_sync, req.query, "negative", "|".join(persona_tags))

            raw_ans = result["answer"]
            clean_ans = clean_llm_output(raw_ans)

            return {
                "answer": clean_ans,
                "thoughts": [],
                "persona": result.get("persona", []),
                "arm_idx": result.get("arm_idx", -1),
                "context_vec": result.get("context_vec", []),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/summary")
async def dashboard_summary():
    """聚合近期工单，生成 AI 矛盾日报摘要"""
    try:
        with memory_lock:
            vs = global_memory["vectorstore"]
        
        if not vs:
            return {"markdown": "Current database is empty, no summary available."}
            
        # 检索最近的 N 条记录 (这里简单取前 20 条用于总结)
        docs = vs.get(limit=20, include=["documents"])
        context = "\n---\n".join(docs["documents"])
        
        llm = ChatTongyi(model="qwen-plus", temperature=0.3)
        prompt = f"""
You are a professional game ops expert. Based on the following recent player feedback, generate a "Daily Community Conflict Report".
Requirements:
1. Use Markdown format.
2. Include: Core Conflict Summary, Impact Scope, Operational Recommendations.
3. Professional and concise tone.

[Feedback Fragments]:
{context}
"""
        res = await run_in_threadpool(llm.invoke, prompt)
        return {"markdown": res.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/dashboard/tickets")
async def get_dashboard_tickets(role: str = None):
    """
    获取工单列表。支持按推荐角色进行实时过滤。
    """
    try:
        with memory_lock:
            vs = global_memory["vectorstore"]
            
        if not vs:
            return {"tickets": []}
            
        # 获取所有带 metadata 的记录
        data = vs.get(include=["metadatas", "documents"])
        tickets = []
        
        for i in range(len(data["ids"])):
            meta = data["metadatas"][i]
            # 如果 event_json 存在，优先解析它
            if "event_json" in meta:
                ticket_data = json.loads(meta["event_json"])
                # 这种动态过滤逻辑可以在前端做，也可以后端做
                tickets.append(ticket_data)
        
        # 简单模拟：如果 URL 传了 role，我们这里可以做一次过滤（实际推荐结果应存储在 metadata 中）
        # 目前阶段我们假设前端负责根据推荐结果进行高亮
        return {"tickets": tickets[::-1]} # 返回按时间倒序
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/feedback")
async def explicit_feedback(req: FeedbackRequest):
    """接收前端传回的点赞或点踩，作为 LinUCB 的显式奖励"""
    try:
        from algorithms.linucb import linucb_agent
        linucb_agent.update(req.arm_idx, req.context_vec, req.reward)
        return {"status": "success", "message": "Feedback received and LinUCB updated."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class RecommendationFeedback(BaseModel):
    arm_idx: int
    context_vec: list
    reward: float  # 1 为有用/处理，0 为忽略

@app.post("/api/v1/recommendation/reward")
async def recommendation_reward(req: RecommendationFeedback):
    """接收运营人员对分发结果的实时反馈，更新 LinUCB 权重"""
    try:
        # 直接调用重构后的 recommender 实例进行增量学习
        ticket_recommender.update_reward(req.arm_idx, req.context_vec, req.reward)
        return {"status": "success", "message": f"Operator feedback recorded for arm {req.arm_idx}."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

