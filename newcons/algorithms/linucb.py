import numpy as np
import threading

class TicketRecommenderLinUCB:
    """针对工单推荐优化的 LinUCB 引擎"""
    def __init__(self, alpha=0.1, feature_dim=20):
        self.alpha = alpha
        self.feature_dim = feature_dim
        
        # 定义职能手臂 (Operators)
        self.operators = [
            "Comm_Specialist",   # 商业化运营 (负责充值、道具反馈)
            "PR_Specialist",     # 公关舆情 (负责辱骂、黑产、排雷)
            "Content_Planner",   # 活动策划 (负责关卡、剧情、建议)
            "Tech_Support"       # 技术维护 (负责闪退、Bug、渲染错误)
        ]
        self.n_arms = len(self.operators)
        
        # 算法状态 A: (n_arms, d, d) 恒等矩阵 ba: (n_arms, d) 零向量
        self.Aa = {i: np.identity(self.feature_dim) for i in range(self.n_arms)}
        self.ba = {i: np.zeros(self.feature_dim) for i in range(self.n_arms)}
        self.lock = threading.Lock()

    def build_context(self, embedding: list, sentiment_score: int, tags: list) -> np.ndarray:
        """
        特征工程：构造 20 维上下文向量
        1. 16维: Embedding 切片 (假设已经降维或取前16位核心特征)
        2. 1维: 归一化情绪分 (score/5)
        3. 3维: 标签索引特征 (取特定业务关键词的命中情况)
        """
        # 截取/补齐 Embedding
        emb_part = np.array(embedding[:16])
        if len(emb_part) < 16:
            emb_part = np.pad(emb_part, (0, 16 - len(emb_part)))
            
        # 归一化情绪
        s_part = np.array([sentiment_score / 5.0])
        
        # 标签转化 (简单语义分类)
        tag_str = "|".join(tags).lower()
        t_part = np.zeros(3)
        if any(w in tag_str for w in ["充值", "钱", "金币", "payment"]): t_part[0] = 1.0
        if any(w in tag_str for w in ["bug", "死机", "报错", "error"]): t_part[1] = 1.0
        if any(w in tag_str for w in ["策划", "建议", "关卡", "难度"]): t_part[2] = 1.0
        
        return np.concatenate([emb_part, s_part, t_part])

    def recommend(self, context_vec: np.ndarray):
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

    def update_reward(self, arm_idx: int, x_t: list, reward: float):
        """
        更新模型反馈
        reward=1: 运营处理了工单或点击查看
        reward=0: 运营忽略了该推荐
        """
        with self.lock:
            x_t = np.array(x_t)
            self.Aa[arm_idx] += np.outer(x_t, x_t)
            self.ba[arm_idx] += reward * x_t

# 单例模式
ticket_recommender = TicketRecommenderLinUCB(alpha=0.2, feature_dim=20)
linucb_agent = ticket_recommender # Legacy alias