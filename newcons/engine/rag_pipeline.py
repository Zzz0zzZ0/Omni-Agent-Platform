"""
RAG 混合检索管线 — 租户感知化。
接受 VectorStoreManager 和 DomainPlugin 作为参数，不再依赖全局状态。
"""
import concurrent.futures

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from algorithms.linucb import LinUCBRecommender
from algorithms.prf import algo_pseudo_relevance_feedback
from algorithms.mmr import algo_mmr_rerank
from core.logger import log


def get_llm(model_type: str = "cloud", temp: float = 0.1):
    """根据 provider 创建 LLM 实例"""
    if model_type == "local":
        from langchain_ollama import ChatOllama
        return ChatOllama(model="qwen3:8b", temperature=temp)
    else:
        from langchain_community.chat_models import ChatTongyi
        return ChatTongyi(model="qwen-plus", temperature=temp)


def get_answer_complex(
    vectorstore,
    bm25_retriever,
    question: str,
    embeddings,
    linucb: LinUCBRecommender | None = None,
    perception_fn=None,
    k_param: int = 3,
    temp_param: float = 0.1,
    alpha: float = 0.5,
    model_type: str = "cloud",
    use_multiquery: bool = False,
    use_rerank: bool = False,
    use_auto_alpha: bool = False,
    use_emotion: bool = False,
):
    """核心单步检索回路"""
    emotion_label = "neutral"
    extracted_entities = []
    player_persona = []

    # 0. NLP 感知
    if use_emotion and perception_fn:
        emotion_label, extracted_entities, player_persona = perception_fn(
            question, model_type=model_type, temp_val=temp_param
        )

    # 1. LLM
    llm = get_llm(model_type, temp_param)

    # 2. LinUCB
    final_alpha = alpha
    arm_idx = -1
    context_vec = None
    if use_auto_alpha and linucb:
        q_vec = embeddings.embed_query(question)
        arm_idx, final_alpha, context_vec = linucb.select_arm(q_vec)

    # 3. 混合检索
    initial_docs = []
    seen_contents = set()

    if vectorstore is not None and bm25_retriever is not None:
        chroma_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            future_vs = executor.submit(chroma_retriever.invoke, question)
            future_bm25 = executor.submit(bm25_retriever.invoke, question)
            docs_vs = future_vs.result()
            docs_bm25 = future_bm25.result()

        k_vs = max(1, int(15 * final_alpha))
        k_bm25 = max(1, int(15 * (1 - final_alpha)))

        for doc in docs_vs[:k_vs] + docs_bm25[:k_bm25]:
            if doc.page_content not in seen_contents:
                initial_docs.append(doc)
                seen_contents.add(doc.page_content)

    # 4. PRF
    search_queries = [question]
    if use_multiquery and initial_docs:
        search_queries = algo_pseudo_relevance_feedback(question, initial_docs)
    unique_docs = list({doc.page_content: doc for doc in initial_docs}.values())

    # 5. MMR 重排序
    final_docs = (
        algo_mmr_rerank(question, unique_docs, embeddings, k_param=k_param)
        if use_rerank and unique_docs
        else unique_docs[:k_param]
    )

    # 6. 生成
    tone_instruction = (
        "User detected as anxious. Use calm and soothing tone."
        if emotion_label == "negative"
        else ""
    )

    if final_docs:
        system_prompt = (
            f"You are a cognitive agent. {tone_instruction}\n"
            f"Answer based on memory fragments.\n\n[Memory Fragments]:\n{{context}}"
        )
        context_text = "\n\n".join([d.page_content for d in final_docs])
    else:
        system_prompt = (
            f"You are a professional game ops cognitive agent. {tone_instruction}\n"
            f"Please answer based on your knowledge base."
        )
        context_text = "(No external memory found)"

    prompt = ChatPromptTemplate.from_template(system_prompt + "\n\n问题: {input}")
    res = (prompt | llm).invoke({"input": question, "context": context_text})
    answer = res.content if hasattr(res, "content") else str(res)

    return {
        "answer": answer,
        "context": final_docs,
        "generated_queries": search_queries,
        "used_alpha": final_alpha,
        "emotion": emotion_label,
        "entities": extracted_entities,
        "persona": player_persona,
        "arm_idx": arm_idx,
        "context_vec": context_vec,
    }


# ── LocalKnowledgeTool (供 Agent 调用) ──────────────────────────

class LocalSearchInput(BaseModel):
    query: str = Field(description="需要搜索的具体问题字符串")


class LocalKnowledgeTool:
    def __init__(self, vectorstore, bm25_retriever, embeddings, linucb=None, **kwargs):
        self.vectorstore = vectorstore
        self.bm25_retriever = bm25_retriever
        self.embeddings = embeddings
        self.linucb = linucb
        self.config = kwargs

    def _run_search(self, query: str) -> str:
        result = get_answer_complex(
            self.vectorstore,
            self.bm25_retriever,
            query,
            embeddings=self.embeddings,
            linucb=self.linucb,
            **self.config,
        )
        docs_text = "\n".join([f"- {d.page_content}" for d in result["context"]])
        return f"[Conclusion]: {result['answer']}\n[References]:\n{docs_text}\n"

    def get_tool(self) -> StructuredTool:
        return StructuredTool.from_function(
            func=self._run_search,
            name="local_knowledge_base",
            description="查询内部文档时调用。",
            args_schema=LocalSearchInput,
        )
