# Omni Agent Platform - 多租户智能运营与工单平台

一个基于大模型的多租户智能运营与客诉处理系统，支持不同业务场景（如游戏、电商等）的灵活扩展，提供意图识别、工单路由及知识库检索功能。

## 核心功能与架构

### 1. 多租户支持 (Multi-Tenancy)
- **API Key 鉴权**：通过 `X-API-Key` 识别租户身份，注入 `TenantContext` 上下文。
- **数据隔离**：SQLite 关系型数据和 ChromaDB 向量数据均基于 `tenant_id` 区分，保障各个业务方的数据独立性。
- **WebSocket 通信**：基于租户维度维护 WebSocket 连接池，确保实时通知（如工单状态更新）仅推送到对应租户的客户端。

### 2. 业务场景扩展 (Domain Plugin System)
通过定义 `DomainPlugin` 接口，系统可以将不同业务的逻辑解耦并独立配置。
以默认的 `GameOpsDomainPlugin` 为例，它注入了：
- 业务专属工具（如抽卡计算器、社区反馈分析）
- 定制化的 Pydantic Schema（用于大模型结构化输出）
- 业务专属 Prompt（用于情绪提取和工单打标）
- LinUCB 推荐引擎所需的候选人/角色列表

### 3. Next.js 前端看板
- 使用 Next.js App Router 构建前端系统。
- 采用深色主题 UI，提供数据汇总、工单列表和历史记录功能。
- 封装 WebSocket React Hook，支持实时的前后端双向通信。
- 封装 API Client，自动处理请求拦截和 Token 传递。

### 4. 算法与检索模块
- **混合检索 (RAG)**：将原有的向量库改造为支持按租户隔离，提供基于 ChromaDB 的本地知识库文档解析和查询功能。
- **强化学习分发 (LinUCB)**：改进 LinUCB 上下文推荐算法，为不同租户维护独立的 Bandit 状态，基于运营人员的反馈动态调整推荐策略。

## 快速启动

### 后端 (FastAPI + LangGraph)
1. 安装依赖:
```bash
pip install -e .
```
2. 复制配置并填入 API Key:
```bash
cp .env.example .env
```
3. 启动服务:
```bash
python newcons/main.py
```

### 前端 (Next.js)
1. 安装依赖:
```bash
cd dashboard-ui
npm install
```
2. 启动开发环境:
```bash
npm run dev
```

## 目录结构
- `newcons/core/`: 配置、数据库、租户上下文、认证逻辑
- `newcons/domains/`: 业务插件定义与实现
- `newcons/engine/`: 向量存储、混合检索、多模态解析管线
- `newcons/algorithms/`: LinUCB 与检索算法实现
- `newcons/agent/`: LangGraph 状态图与处理流水线
- `newcons/services/`: 业务逻辑层（Service 层）
- `newcons/api/`: FastAPI 路由端点
- `dashboard-ui/`: Next.js 前端项目

## 如何接入新业务线
1. 在 `newcons/domains/` 创建新业务目录。
2. 实现 `DomainPlugin` 接口。
3. 定义业务专属的 Tools、Prompts 和 Schemas。
4. 在 `newcons/domains/registry.py` 中注册该插件。
