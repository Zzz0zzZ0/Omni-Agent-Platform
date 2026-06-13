"""
LinUCB Contextual Bandit 推荐引擎。
已移除全局单例 — 每个 tenant 持有独立实例，由 Service 层管理生命周期。
"""
import numpy as np
import threading


class LinUCBRecommender:
    """通用 LinUCB 推荐器，运营角色与标签关键词由外部注入。"""

    def __init__(
        self,
        operators: list[str],
        tag_keywords: dict[int, list[str]],
        alpha: float = 0.2,
        emb_dim: int = 16,
    ):
        self.operators = operators
        self.tag_keywords = tag_keywords  # {dim_idx: [keywords]}
        self.alpha = alpha
        self.n_tags = len(tag_keywords)
        self.feature_dim = emb_dim + 1 + self.n_tags  # emb + sentiment + tags
        self.n_arms = len(operators)

        self.Aa = {i: np.identity(self.feature_dim) for i in range(self.n_arms)}
        self.ba = {i: np.zeros(self.feature_dim) for i in range(self.n_arms)}
        self.lock = threading.Lock()

    def build_context(self, embedding: list, sentiment_score: int, tags: list) -> np.ndarray:
        """构造上下文向量: [embedding_slice | normalized_sentiment | tag_features]"""
        emb_dim = self.feature_dim - 1 - self.n_tags
        emb_part = np.array(embedding[:emb_dim])
        if len(emb_part) < emb_dim:
            emb_part = np.pad(emb_part, (0, emb_dim - len(emb_part)))

        s_part = np.array([sentiment_score / 5.0])

        tag_str = "|".join(tags).lower()
        t_part = np.zeros(self.n_tags)
        for idx, keywords in self.tag_keywords.items():
            if idx < self.n_tags and any(w in tag_str for w in keywords):
                t_part[idx] = 1.0

        return np.concatenate([emb_part, s_part, t_part])

    def recommend(self, context_vec: np.ndarray) -> tuple[str, int, list]:
        """选择最合适的运营人员"""
        with self.lock:
            p_t = np.zeros(self.n_arms)
            for i in range(self.n_arms):
                A_inv = np.linalg.inv(self.Aa[i])
                theta_hat = A_inv.dot(self.ba[i])
                uncertainty = self.alpha * np.sqrt(context_vec.dot(A_inv).dot(context_vec))
                p_t[i] = theta_hat.dot(context_vec) + uncertainty

            best_idx = int(np.argmax(p_t))
            return self.operators[best_idx], best_idx, context_vec.tolist()

    def select_arm(self, query_embedding: list) -> tuple[int, float, list]:
        """为 RAG 混合检索选择 alpha 权重 (双臂: vector vs bm25)"""
        emb_dim = self.feature_dim - 1 - self.n_tags
        emb_part = np.array(query_embedding[:emb_dim])
        if len(emb_part) < emb_dim:
            emb_part = np.pad(emb_part, (0, emb_dim - len(emb_part)))

        context_vec = np.concatenate([emb_part, np.zeros(1 + self.n_tags)])

        with self.lock:
            # 简化为双臂: 0=偏向向量, 1=偏向BM25
            p_t = np.zeros(2)
            for i in range(min(2, self.n_arms)):
                A_inv = np.linalg.inv(self.Aa[i])
                theta_hat = A_inv.dot(self.ba[i])
                uncertainty = self.alpha * np.sqrt(context_vec.dot(A_inv).dot(context_vec))
                p_t[i] = theta_hat.dot(context_vec) + uncertainty

            arm_idx = int(np.argmax(p_t))
            alpha_val = 0.7 if arm_idx == 0 else 0.3
            return arm_idx, alpha_val, context_vec.tolist()

    def update_reward(self, arm_idx: int, x_t: list, reward: float) -> None:
        """更新模型反馈"""
        with self.lock:
            x_t = np.array(x_t)
            if arm_idx < self.n_arms:
                self.Aa[arm_idx] += np.outer(x_t, x_t)
                self.ba[arm_idx] += reward * x_t