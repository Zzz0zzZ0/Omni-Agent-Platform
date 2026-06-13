"""
向量存储管理器 — per-tenant Chroma collection 隔离。
替代旧版全局 embeddings 单例 + 硬路径 persist_dir。
"""
import os
from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from langchain_core.documents import Document

from core.settings import settings
from core.tenant import TenantContext
from core.logger import log


class EmbeddingProvider:
    """Lazy singleton — 模型全局共享，collection 按 tenant 隔离"""
    _instance = None

    @classmethod
    def get(cls) -> HuggingFaceEmbeddings:
        if cls._instance is None:
            log.info(f"Loading embedding model: {settings.embed_model_name}")
            try:
                cls._instance = HuggingFaceEmbeddings(model_name=settings.embed_model_name)
            except Exception as e:
                log.warning(f"Failed to load HF embeddings ({e}). Falling back to FakeEmbeddings.")
                from langchain_core.embeddings import FakeEmbeddings
                cls._instance = FakeEmbeddings(size=1024)
        return cls._instance


class VectorStoreManager:
    """Per-tenant 向量存储管理"""

    def __init__(self, tenant_ctx: TenantContext):
        self.tenant_ctx = tenant_ctx
        self.embeddings = EmbeddingProvider.get()
        self._vectorstore = None
        self._bm25 = None
        self._all_splits = []

    @property
    def persist_dir(self) -> str:
        return self.tenant_ctx.chroma_persist_dir

    def get_vectorstore(self) -> Chroma | None:
        """获取或创建 tenant 的 Chroma 实例"""
        if self._vectorstore is None and os.path.exists(self.persist_dir):
            self._vectorstore = Chroma(
                collection_name=self.tenant_ctx.chroma_collection_name,
                embedding_function=self.embeddings,
                persist_directory=self.persist_dir,
            )
        return self._vectorstore

    def get_bm25(self) -> BM25Retriever | None:
        return self._bm25

    def ingest_file(self, file_path: str) -> tuple[Chroma, list, int]:
        """构建混合索引 (Chroma + BM25)"""
        os.makedirs(self.persist_dir, exist_ok=True)

        if file_path.endswith(".pdf"):
            loader = PyPDFLoader(file_path)
            docs = loader.load()
        else:
            docs = None
            for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
                try:
                    loader = TextLoader(file_path, encoding=encoding)
                    docs = loader.load()
                    break
                except (UnicodeDecodeError, Exception) as e:
                    if encoding == "latin-1":
                        raise ValueError(f"无法使用任何编码读取文件 {file_path}: {str(e)}")
                    continue

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=300, chunk_overlap=50)
        splits = text_splitter.split_documents(docs)

        self._vectorstore = Chroma.from_documents(
            splits,
            self.embeddings,
            collection_name=self.tenant_ctx.chroma_collection_name,
            persist_directory=self.persist_dir,
        )

        self._all_splits.extend(splits)
        if self._all_splits:
            self._bm25 = BM25Retriever.from_documents(self._all_splits)
            self._bm25.k = 10

        log.info(f"[Tenant:{self.tenant_ctx.tenant_id}] Ingested {len(splits)} fragments from {file_path}")
        return self._vectorstore, splits, len(splits)

    def add_document(self, doc: Document) -> bool:
        """向现有向量库追加单个文档"""
        if self._vectorstore is not None:
            self._vectorstore.add_documents([doc])
            self._all_splits.append(doc)
            # 重建 BM25
            if self._all_splits:
                self._bm25 = BM25Retriever.from_documents(self._all_splits)
                self._bm25.k = 10
            return True
        return False

    def visualize_semantic_space(self):
        """降维可视化语义空间"""
        from sklearn.decomposition import PCA
        import pandas as pd

        if self._vectorstore is None:
            return None
        data = self._vectorstore.get(include=["embeddings", "documents"])
        if len(data["embeddings"]) < 3:
            return None

        reducer = PCA(n_components=2)
        vecs_2d = reducer.fit_transform(data["embeddings"])
        df = pd.DataFrame(vecs_2d, columns=["x", "y"])
        df["text"] = [t[:50] + "..." for t in data["documents"]]
        return df
