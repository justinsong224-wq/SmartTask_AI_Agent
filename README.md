# SmartTask AI Agent

<div align="center">

![SmartTask AI Agent](https://smarttaskaiagent-production.up.railway.app/icons/icon-192x192.png)

**一个具备多工具调用、双层记忆系统和云端部署的全栈 AI Agent**

[![Railway](https://img.shields.io/badge/部署-Railway-blueviolet?logo=railway)](https://smarttaskaiagent-production.up.railway.app)
[![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)](https://python.org)
[![Vue](https://img.shields.io/badge/Vue-3.0-42b883?logo=vue.js)](https://vuejs.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-latest-009688?logo=fastapi)](https://fastapi.tiangolo.com)

[🚀 在线体验](https://smarttaskaiagent-production.up.railway.app) · [📦 GitHub 仓库](https://github.com/justinsong224-wq/SmartTask_AI_Agent)

</div>

---

## 项目简介

SmartTask AI Agent 是一个**完全自研**的 AI Agent 系统，不依赖 LangChain 等框架，从零实现了 Agent Loop 的核心机制：任务规划（Planner）→ 工具执行（Executor）→ 记忆管理（Memory）→ 结构化输出（Formatter）。

系统接入阿里云 DashScope Qwen 大语言模型，支持网络搜索、数学计算、文件读写等多种工具，并通过 Redis + SQLite 实现了短期与长期的双层记忆架构，最终部署到 Railway 云平台，支持 PWA 安装为桌面应用。

---

## 技术架构

```
用户输入
   ↓
Vue 3 前端 (Element Plus)
   ↓  HTTP
FastAPI 后端
   ↓
┌─────────────────────────────────┐
│          Agent Loop             │
│  Planner → Executor → Formatter │
│         ↕                       │
│      Memory Manager             │
│  Redis (短期) + SQLite (长期)    │
└─────────────────────────────────┘
   ↓
工具系统
├── 🔍 网络搜索 (Serper.dev)
├── 🧮 安全计算器 (AST 白名单)
└── 📁 文件读写 (aiofiles)
   ↓
Qwen-turbo (阿里云 DashScope)
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 大语言模型 | 阿里云 DashScope Qwen-turbo |
| Agent 框架 | 纯 Python 自研（不依赖 LangChain） |
| API 服务 | FastAPI + Uvicorn |
| 短期记忆 | Redis（TTL 自动过期） |
| 长期记忆 | SQLite + LLM 智能筛选 |
| 网络搜索 | Serper.dev（Google 搜索 API） |
| 计算工具 | Python AST 白名单安全计算 |
| 文件工具 | aiofiles 异步读写 |
| 前端 | Vue 3 + Vite + Element Plus |
| 部署 | Railway（前端 + 后端 + Redis） |
| 本地开发 | Docker Compose |

---

## 核心功能

### 🤖 自研 Agent Loop
不依赖任何 Agent 框架，手动实现完整的 Planner → Executor → Formatter 流程，深入理解 Agent 工作原理。

### 🛠️ 多工具系统
- **网络搜索**：接入 Serper.dev，实时获取 Google 搜索结果
- **安全计算器**：基于 AST 白名单机制，防止代码注入，支持复杂数学运算
- **文件读写**：异步文件操作，内置路径穿越防护

### 🧠 双层记忆架构
- **短期记忆（Redis）**：保存当前会话上下文，TTL 自动过期，支持多会话隔离
- **长期记忆（SQLite）**：持久化重要任务结果，支持关键词检索
- **LLM 智能筛选**：由 Qwen 自动判断任务是否值得长期记忆，避免垃圾数据

### 📱 PWA 支持
支持安装为桌面/移动端应用，提供原生 App 体验。

---

## 项目结构

```
smarttask-agent/
├── agent-core/                 # 后端服务
│   ├── agent/
│   │   ├── loop.py            # Agent 主循环
│   │   ├── planner.py         # 任务规划器
│   │   ├── executor.py        # 步骤执行器
│   │   └── formatter.py       # 结果格式化
│   ├── llm/
│   │   ├── client.py          # LLM 统一封装
│   │   ├── prompts.py         # Prompt 模板
│   │   └── parser.py          # JSON 容错解析
│   ├── tools/
│   │   ├── registry.py        # 工具注册中心
│   │   ├── search.py          # 网络搜索
│   │   ├── calculator.py      # 安全计算器
│   │   └── file_tool.py       # 文件读写
│   ├── memory/
│   │   ├── short_term.py      # Redis 短期记忆
│   │   └── long_term.py       # SQLite 长期记忆
│   └── api/
│       ├── routes.py          # API 路由
│       └── schemas.py         # 数据模型
└── frontend/                  # 前端服务
    └── src/
        ├── App.vue            # 主界面
        └── api/agent.js       # API 封装
```

---

## 本地开发

### 前置条件
- Docker & Docker Compose
- Node.js 20+
- 阿里云 DashScope API Key
- Serper.dev API Key

### 启动步骤

**1. 克隆仓库**
```bash
git clone https://github.com/justinsong224-wq/SmartTask_AI_Agent.git
cd SmartTask_AI_Agent
```

**2. 配置环境变量**
```bash
cp .env.example .env
# 编辑 .env，填入你的 API Key
```

**3. 启动后端（Docker Compose）**
```bash
docker-compose up -d
```

**4. 启动前端**
```bash
cd frontend
npm install
npm run dev
```

**5. 访问**

打开浏览器访问 `http://localhost:5173`

### 环境变量说明

```bash
DASHSCOPE_API_KEY=    # 阿里云 DashScope API Key
SERPER_API_KEY=       # Serper.dev API Key
LLM_PROVIDER=dashscope
LLM_MODEL=qwen-turbo
AGENT_MAX_STEPS=10
AGENT_TIMEOUT=60
REDIS_URL=redis://redis:6379/0
REDIS_TTL=3600
FILE_BASE_DIR=/app/data/files
```

---

## API 接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/agent/run` | 执行 Agent 任务 |
| GET | `/api/memory/long-term` | 查询长期记忆 |
| DELETE | `/api/memory/long-term` | 清空长期记忆 |
| GET | `/api/memory/short-term/{session_id}` | 查询会话记忆 |
| DELETE | `/api/memory/short-term/{session_id}` | 清空会话记忆 |
| GET | `/api/memory/sessions` | 获取所有会话 |
| GET | `/api/memory/long-term/stats` | 记忆统计信息 |
| GET | `/health` | 健康检查 |

---

## 开发亮点

- **零框架依赖**：Agent Loop 完全自研，不依赖 LangChain / AutoGPT 等，深度理解 Agent 底层机制
- **安全设计**：计算器使用 AST 白名单防止代码注入；文件工具内置路径穿越防护
- **容错解析**：自研 JSON 容错解析器，处理 LLM 输出格式不稳定的问题
- **云原生部署**：前端 + 后端 + Redis 全部部署在 Railway，支持 PWA 安装

---

## 作者

**Justin Song** · [GitHub](https://github.com/justinsong224-wq)