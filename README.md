# 🎮 Honkai Agent Platform: ToB 级游戏运营 AI 看板与智能体系统

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![React](https://img.shields.io/badge/React-18+-61dafb.svg)
![DashScope](https://img.shields.io/badge/Alibaba-DashScope-orange.svg)
![Tailwind](https://img.shields.io/badge/Tailwind-CSS-38b2ac.svg)

本项目是一款专为《崩坏：星穹铁道》等高并发二次元游戏打造的 **ToB 级运营数据看板与自动化客诉处理系统**。系统深度融合了多模态感知、自适应 RAG 检索与个性化强化学习推荐算法，将零散的玩家反馈转化为可闭环的运营决策。

---

## 🌟 核心技术亮点

### 1. 国产化大模型底座 (Alibaba DashScope)
- **核心引擎**: 全链路接入 **阿里云百炼 (通义千问 Qwen-Plus)**，在语义理解、长文本摘要以及 Agent 逻辑编排上实现了高可用与低延迟。
- **搜索增强**: 移除了海外 Tavily 依赖，采用 **DuckDuckGo Search** 自动化工具，实现零成本的外网实时更新。

### 2. 专业级 ToB 数据看板 (React + Vite + Tailwind)
- **身份感知控制面板**: 模拟真实业务场景，支持 [商业化]、[公关]、[策划]、[技术] 四类运营身份的动态切换。
- **AI 矛盾日报**: 利用 Qwen-Plus 的长文本能力，实时从海量反馈中提炼“今日全服核心冲突”，并给出运营建议。
- **互动式工单流**: 配合玻璃拟态（Glassmorphism）设计，提供实时的 OCR 图文展示与 AI 决策逻辑复现。

### 3. 海马体：自适应混合检索引擎 (Hybrid RAG + LinUCB)
- **自适应权重 (LinUCB)**: 业内领先的 Contextual Bandit 架构。系统根据玩家 Query 的特征，**实时、动态**调节向量检索（Chroma）与词频检索（BM25）的 Alpha 权重。
- **精细化推荐**: 系统会根据运营人员的点击行为，通过 LinUCB 进行在线增量学习，确保“最紧急、最对口”的工单精准分发给最合适的运营身份。

### 4. 自动化管线 (LangGraph Pipeline)
- **双 Agent 审查**: 情绪审查员 (Sentiment) + 标签路由员 (Router) 协作，利用 Pydantic 结构化输出确保 100% 的机器可解释性。
- **多模态感知**: 集成 PaddleOCR 与 Docling，支持玩家截图反馈的结构化解析。

---

## 📁 模块化项目结构

```text
dashboard-ui/           # React 前端工程 (Vite + Tailwind)
newcons/
├── agent/
│   ├── graph_brain.py  # LangGraph 多步决策大脑 (DuckDuckGo 增强)
│   ├── ticket_pipeline.py # 自动化工单处理流水线
│   └── tools.py        # 业务专属 Agent 工具集
├── algorithms/
│   ├── linucb.py       # 强化学习推荐引擎 (Contextual Bandit)
│   └── ...             # MMR / PRF 等 RAG 优化算法
├── api/
│   └── server.py       # FastAPI 高性能后端 (接入阿里云百炼)
├── engine/
│   ├── vector_store.py # Chroma 混合向量记忆体
│   └── rag_pipeline.py # 点击闭环的 RAG 检索流程
└── perception/
    └── nlp_pipeline.py # 多模态语义感知 (Qwen 驱动)
```

---

## 🚀 快速启动指南

### 1. 安装依赖

```bash
# 后端依赖
pip install -r requirements.txt

# 前端依赖
cd dashboard-ui
npm install
```

### 2. 环境配置
在根目录创建 `.env` 文件：
```env
DASHSCOPE_API_KEY=您的阿里云百炼API密钥
```

### 3. 启动全链路

**一键启动后端 (Port 8000):**
```bash
cd newcons
python api/server.py
```

**一键启动前端 (Port 5173):**
```bash
cd dashboard-ui
npm run dev
```

---

## 🏗️ 技术栈预览
- **推理层**: 阿里云百炼 (Qwen-Plus), LangChain, LangGraph
- **存储层**: ChromaDB (Vector), SQLite (Log)
- **前端层**: React, Tailwind CSS, Lucide Icons, Vite
- **算法层**: Scikit-Learn (PCA), LinUCB, BM25, MMR, PRF
- **多模态**: PaddleOCR, Docling

---

## 📊 路线图 (Roadmap)
- [x] 基于 React 的 ToB 看板重构
- [x] 阿里云百炼 (DashScope) 全栈适配
- [x] 强化学习 (LinUCB) 推荐奖励闭环
- [ ] 实时语音客诉接入
- [ ] 自动化 PR 公告导出 (PDF)
