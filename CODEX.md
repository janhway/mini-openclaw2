# PRD：Mini-OpenClaw（本地透明 Agent）

## 0. 目标与非目标

### 0.1 目标

* 构建一个**本地运行**的透明 AI Agent：对话、工具调用、记忆读写全可追踪、可编辑。
* Skills 以**文件夹插件**形式存在，Agent 必须通过 `read_file` 读取 `SKILL.md` 学习并执行。
* System Prompt 由本地文件动态拼接，且具备截断策略。
* 提供后端 FastAPI API（含 SSE 流式输出），前端 Next.js 14 IDE 三栏 UI（Sidebar/Stage/Inspector）。

### 0.2 非目标（明确不做）

* 不构建 SaaS / 多租户平台。
* 不引入 MySQL/Redis 等重型依赖。
* 不把“技能”实现为预置 python function（严格 Instruction-following，不 Function-calling skill）。

---

## 1. 用户故事（MVP）

### 1.1 核心对话

* 作为用户，我输入消息，得到 Agent 回复。
* 我能看到 Agent 过程中：思考片段 / 工具调用 / 读取的文件路径（以 SSE 流式推送）。
* 我能选择一个会话继续对话。

### 1.2 Skills 使用

* 作为用户，我新增一个技能（把一个新文件夹拖进 `backend/skills/xxx/`，其中有 `SKILL.md`）。
* Agent 下次会话开始时能识别到新技能，并能在对话中根据请求选用它。
* Agent 必须先 `read_file(location)`，再按技能里写的步骤调用 core tools。

### 1.3 记忆与可编辑性

* 作为用户，我能在右侧 Monaco Editor 打开/编辑 `MEMORY.md` 或当前用到的 `SKILL.md`。
* 修改保存后，下一次对话中 Prompt 拼接应反映更新内容。

### 1.4 文件管理与会话管理

* 作为用户，我能拉取会话列表、加载某个会话历史。
* 作为用户，我能读取/保存指定文件内容（只允许项目内路径，禁止越权）。

---

## 2. 系统架构

### 2.1 组件

* **Backend（FastAPI）**：Agent 编排、工具执行、文件读写、会话存储、SSE 输出。
* **Frontend（Next.js 14）**：IDE 三栏 UI、SSE 客户端、Monaco 编辑器、会话与文件浏览。
* **Storage（本地文件系统）**：`memory/`、`sessions/`、`skills/`、`storage/`（RAG 索引）等。

### 2.2 关键原则（必须）

* **File-first**：所有记忆/配置/技能均以 Markdown/JSON 存本地。
* **透明**：工具调用与文件读写必须记录并可回放。
* **安全沙箱**：Shell 与 ReadFile 必须限定 `root_dir`；Fetch 需清洗 HTML 减 token。
* **技能协议**：Agent 不调用 `get_weather()` 这类函数；只通过读取技能文件学习步骤。

---

## 3. 技术选型与约束（硬性）

### 3.1 后端

* Python 3.10+，强制 Type Hinting
* FastAPI（异步）
* LangChain 1.x stable（必须使用 `create_agent`；禁用 `AgentExecutor`、`create_react_agent`）
* LlamaIndex Core：Hybrid Search（BM25 + Vector Search）+ 本地持久化 `storage/`
* 模型接口：OpenAI API compatible（OpenRouter/DeepSeek/Claude 等）
* 不引入 MySQL/Redis
* Python环境约束使用同目录文件ENV.md
* 后端要用到的API服务，比如大模型API-KEY,从同目录文件KEY.md中获取

### 3.2 内置 Core Tools（必须内置 5 个）

1. `terminal`：`langchain_community.tools.ShellTool`（root_dir + 高危命令黑名单）
2. `python_repl`：`langchain_experimental.tools.PythonREPLTool`
3. `fetch_url`：`langchain_community.tools.RequestsGetTool` + wrapper 清洗输出（BeautifulSoup/html2text）
4. `read_file`：`langchain_community.tools.file_management.ReadFileTool`（root_dir 强制）
5. `search_knowledge_base`：LlamaIndex Hybrid Retrieval（scan `knowledge/`，persist `storage/`）

### 3.3 前端

* Next.js 14+ App Router + TypeScript
* Tailwind + shadcn/ui + Lucide
* Monaco Editor（Light theme）
* 三栏布局：Sidebar / Stage / Inspector
* Stage 支持 Collapsible Thoughts（可折叠思考链）
* SSE 实时流式渲染 Thought/Tool/Final

---

## 4. 数据与文件规范

### 4.1 项目路径（后端侧）

* `backend/memory/MEMORY.md`：长期记忆（可编辑）
* `backend/memory/logs/`：daily logs（可选，MVP 可先留空）
* `backend/sessions/{session_name}.json`：会话记录（JSON 数组）
* `backend/skills/*/SKILL.md`：技能说明书（含 frontmatter）
* `backend/workspace/`：System prompt 片段（SOUL/IDENTITY/USER/AGENTS 等）
* `backend/storage/`：RAG 索引持久化目录
* `backend/knowledge/`：RAG 文档目录（PDF/MD/TXT）

### 4.2 sessions 文件格式（建议）

`backend/sessions/{session}.json` 为 JSON 数组，每条：

```json
{
  "type": "user|assistant|tool",
  "ts": "ISO8601",
  "content": "...",
  "tool": { "name": "...", "input": {...}, "output": "..." }
}
```

约束：必须能完整回放 SSE 输出内容（至少保存 tool calls 与 final）。

### 4.3 SKILL.md 规范（最低要求）

* 必须包含 frontmatter：`name`, `description`（以及可选 tags）
* 内容必须包含：

  * 触发条件/适用范围
  * 执行步骤（明确写出用哪些 Core Tools，示例命令/代码）
  * 输出格式要求

示例 frontmatter（建议）：

```yaml
---
name: get_weather
description: 获取指定城市的实时天气信息
---
```

### 4.4 SKILLS_SNAPSHOT.md（生成规则）

* 启动或新会话开始时扫描 `backend/skills/`
* 读取每个 `SKILL.md` frontmatter
* 生成：

```xml
<available_skills>
  <skill>
    <name>...</name>
    <description>...</description>
    <location>./backend/skills/.../SKILL.md</location>
  </skill>
</available_skills>
```

`location` 必须是相对路径。

---

## 5. System Prompt 拼接规范（必须）

### 5.1 拼接顺序

1. `SKILLS_SNAPSHOT.md`
2. `SOUL.md`
3. `IDENTITY.md`
4. `USER.md`
5. `AGENTS.md`
6. `MEMORY.md`

### 5.2 截断策略

* 若拼接后 token 超限，或单文件 > 20k 字符：

  * 截断超长部分
  * 在末尾追加 `...[truncated]`
* 规则建议：优先保留前部（SKILLS/SOUL/IDENTITY），其次 USER/AGENTS，最后 MEMORY 可截断更多。

### 5.3 AGENTS.md 必须包含元指令（强制）

核心：技能调用协议（必须先 read_file location；禁止猜参数；再用 core tools 执行）

---

## 6. 后端 API（FastAPI）

### 6.1 基本信息

* Port：8002
* Base URL：`http://localhost:8002`

### 6.2 `POST /api/chat`（核心）

**Request**

```json
{
  "message": "string",
  "session_id": "string",
  "stream": true
}
```

**Response**

* 当 `stream=true`：SSE（Server-Sent Events）

  * 必须推送事件类型：`thought`, `tool_call`, `tool_result`, `final`, `error`（至少 thought/tool/final）
  * 每条 SSE data 建议为 JSON：

```json
{ "type": "tool_call", "name": "read_file", "input": {"path": "..."} }
```

### 6.3 `GET /api/files`

* Query：`path=memory/MEMORY.md`
* 返回：文件内容（string）
* 安全：path 必须在后端 `root_dir` 下；禁止 `..` 越权

### 6.4 `POST /api/files`

**Body**

```json
{ "path": "string", "content": "string" }
```

* 功能：保存 Memory 或 Skill 文件修改
* 安全：同上（root_dir + allowlist）

### 6.5 `GET /api/sessions`

* 返回：历史会话列表（文件名 + 最近更新时间等）

> （可选增强）`GET /api/sessions/{id}`：直接拿会话完整 JSON。MVP 若不做，前端可直接用 files 接口读 sessions 文件，但更推荐提供独立 endpoint。

---

## 7. 核心执行流程（必须符合）

1. 会话开始 → 扫描 skills → 生成 `SKILLS_SNAPSHOT.md`
2. 拼接 system prompt（6 文件）→ 截断策略
3. Agent 接到用户请求 → 基于 prompt 内 `available_skills` 决策
4. 命中 skill → **第一步必须 `read_file(location)`**
5. 解析 skill 内容 → 按步骤调用 core tools（terminal/python_repl/fetch_url/search_kb）
6. 全过程通过 SSE 推送：读取了哪个文件、调用了什么工具、输出摘要
7. 写入 sessions JSON（含 tool calls 与 final）

---

## 8. 前端需求（Next.js 14）

### 8.1 布局

* 顶部半透明导航栏（左中：mini OpenClaw；)
* 三栏：

  * Sidebar：导航（Chat/Memory/Skills）+ 会话列表
  * Stage：对话流 + Collapsible Thoughts（SSE 思考链可折叠）
  * Inspector：Monaco Editor（Light theme）编辑 `SKILL.md` / `MEMORY.md`

### 8.2 前端与后端交互

* Chat：通过 SSE 订阅 `POST /api/chat`，实时渲染事件
* Sessions：`GET /api/sessions` 列表；点击加载会话
* Files：`GET /api/files` 读取；`POST /api/files` 保存

### 8.3 UI 风格

* `#fafafa` 背景 + frosty glass
* 强调色：Klein Blue 或活力橙
* shadcn/ui 组件体系

---

## 9. 目录结构（最终版）

```
mini-openclaw/
├── backend/
│   ├── app.py
│   ├── memory/
│   │   ├── logs/
│   │   └── MEMORY.md
│   ├── sessions/
│   ├── skills/
│   │   └── get_weather/
│   │       └── SKILL.md
│   ├── knowledge/
│   ├── storage/
│   ├── workspace/
│   │   ├── SOUL.md
│   │   ├── IDENTITY.md
│   │   ├── USER.md
│   │   └── AGENTS.md
│   ├── tools/
│   ├── graph/
│   └── requirements.txt
│
└── frontend/
    └── src/
        ├── app/
        │   ├── layout.tsx
        │   ├── page.tsx
        │   └── globals.css
        ├── components/
        │   ├── layout/      # navbar/sidebar/stage/inspector
        │   ├── chat/        # message/list/input/thought-view
        │   ├── editor/      # monaco wrapper
        │   └── ui/          # shadcn
        ├── features/
        │   ├── chat/        # SSE + store + types
        │   ├── files/
        │   └── sessions/
        ├── lib/             # sse/fetcher
        ├── styles/
        └── types/
```

---

## 10. MVP 交付清单（Codex 执行 Checklist）

### 10.1 后端（必须可跑）

* [ ] FastAPI server 起在 8002
* [ ] 实现 `/api/chat` SSE：至少 thought/tool/final
* [ ] 实现 `/api/files` GET/POST（root_dir 限制）
* [ ] 实现 `/api/sessions`（列出 sessions 文件）
* [ ] skills 扫描 + `SKILLS_SNAPSHOT.md` 生成
* [ ] system prompt 拼接（6 文件 + truncation）
* [ ] core tools 5 个可用（含 fetch wrapper 清洗）
* [ ] sessions 写入（包含 tool calls）

### 10.2 前端（必须可跑）

* [ ] Next.js 14 App Router + Tailwind + shadcn + Lucide
* [ ] 三栏 IDE 布局 + navbar
* [ ] Chat SSE 流式渲染 + Collapsible Thoughts
* [ ] 会话列表加载/切换
* [ ] Monaco Editor 打开/编辑/保存 MEMORY/Skill

### 10.3 示例技能（必须）

* [ ] `get_weather/SKILL.md`（写明用 fetch_url 或 python_repl 的步骤）
* [ ] Agent 能通过 read_file 学习并完成一次天气查询（哪怕用 mock API）

---

## 11. 验收标准（Definition of Done）

1. 启动后端 + 前端，打开 UI：

   * Sidebar 能看到会话列表
   * Stage 可发消息并收到流式输出
   * Inspector 能编辑并保存 MEMORY.md
2. 新增技能文件夹后（写好 SKILL.md frontmatter）：

   * 新会话启动自动刷新 skills snapshot
   * 对话中触发技能，SSE 中能看到 `read_file(location)`
3. 安全：

   * read_file 与 terminal 都不能访问 root_dir 外
   * fetch_url 输出为 Markdown/纯文本（非整页 HTML）

---
