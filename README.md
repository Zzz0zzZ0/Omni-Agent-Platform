# Honkai Agent Platform

> 基于大模型的多租户智能运营与客诉处理平台，支持业务场景插件化扩展。

## 架构概览

```
┌──────────────┐     ┌──────────────────────────────┐
│  Next.js UI  │◄───►│  FastAPI + WebSocket Server  │
│  (dashboard) │     │         (uvicorn)             │
└──────────────┘     └──────┬───────────────────────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
        ┌─────▼────┐  ┌────▼─────┐  ┌────▼──────┐
        │ LangGraph │  │   RAG    │  │  LinUCB   │
        │  Agent    │  │ Pipeline │  │ Recommender│
        └─────┬────┘  └────┬─────┘  └────┬──────┘
              │             │             │
        ┌─────▼─────────────▼─────────────▼──────┐
        │     Domain Plugin System               │
        │  (GameOps / 可扩展至电商、金融等)        │
        └────────────────────────────────────────┘
              │                   │
        ┌─────▼──────┐    ┌──────▼───────┐
        │  SQLite    │    │   ChromaDB   │
        │ (aiosqlite)│    │ (向量存储)    │
        └────────────┘    └──────────────┘
```

## 核心特性

### 多租户隔离
- `X-API-Key` 鉴权 → `TenantContext` 注入
- SQLite 关系数据 + ChromaDB 向量数据按 `tenant_id` 隔离
- WebSocket 连接池按租户维度管理，实时推送工单状态变更

### 业务插件系统 (Domain Plugin)
通过 `DomainPlugin` 接口解耦业务逻辑，每个插件包含：
- 业务专属 Tools（如抽卡计算器、社区反馈分析）
- 定制化 Pydantic Schema（大模型结构化输出）
- 业务 Prompt（情绪提取、工单打标）
- LinUCB 候选人/角色列表

### NLP 感知层 (Perception)
- 集成 DashScope 大模型进行意图识别与情绪分析
- 支持多轮对话上下文理解

### 检索增强生成 (RAG)
- ChromaDB 向量存储 + BGE-M3 嵌入模型
- 多模态文档解析（Docling + PaddleOCR）
- MMR 多样性检索 + PRF 伪相关反馈优化

### 强化学习推荐 (LinUCB)
- 按租户维护独立 Bandit 状态
- 运营人员反馈驱动的动态策略调整

### Next.js 前端看板
- App Router 架构，深色主题 UI
- 数据汇总、工单管理、Pipeline 可视化
- WebSocket Hook 实时双向通信

## 快速启动

### 环境要求
- Python ≥ 3.10
- Node.js ≥ 18

### 后端

```bash
# 安装依赖
pip install -e .

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入 DASHSCOPE_API_KEY

# 启动服务 (默认 :8000)
python newcons/main.py
```

### 前端

```bash
cd dashboard-ui
npm install
npm run dev
# 访问 http://localhost:3000
```

## 项目结构

```
├── newcons/                  # 后端核心
│   ├── main.py               # FastAPI 入口
│   ├── core/                 # 配置、数据库、租户上下文、认证
│   ├── api/                  # REST & WebSocket 路由
│   ├── agent/                # LangGraph 状态图 & Pipeline
│   ├── perception/           # NLP 感知层（意图/情绪）
│   ├── engine/               # 向量存储、RAG、文档解析
│   ├── algorithms/           # LinUCB、MMR、PRF
│   ├── domains/              # 业务插件（GameOps 等）
│   └── services/             # 业务逻辑层
├── dashboard-ui/             # Next.js 前端
│   └── src/
│       ├── app/              # 页面路由
│       ├── components/       # UI 组件
│       ├── hooks/            # WebSocket 等 Hooks
│       └── lib/              # API Client
├── pyproject.toml            # Python 项目配置
└── .env.example              # 环境变量模板
```

## 接入新业务线

1. 在 `newcons/domains/` 下创建新业务目录
2. 实现 `DomainPlugin` 接口（继承 `newcons/domains/base.py`）
3. 定义业务专属的 Tools、Prompts、Schemas
4. 在 `newcons/domains/registry.py` 中注册插件

## 技术栈

| 层级 | 技术 |
|------|------|
| LLM | DashScope (Qwen) / LangChain / LangGraph |
| 后端 | FastAPI + Uvicorn + WebSocket |
| 数据库 | SQLite (aiosqlite) + ChromaDB |
| 嵌入模型 | BGE-M3 (HuggingFace) |
| 文档解析 | Docling + PaddleOCR |
| 前端 | Next.js (App Router) |
| 算法 | LinUCB / MMR / PRF |

## License

MIT
