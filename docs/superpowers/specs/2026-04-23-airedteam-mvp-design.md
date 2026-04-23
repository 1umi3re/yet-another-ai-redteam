# AI Redteam Framework — MVP 设计文档

**日期**：2026-04-23
**状态**：Approved（待 writing-plans 阶段）
**范围**：P0 后端核心闭环 + 前端 MVP（端到端可演示）

---

## 1. 问题陈述

构建一个面向团队（<20 人，内网部署）的低代码/无代码 AI 红队测试框架，支持：
- 通过统一接入层对 OpenAI/Anthropic 兼容的 AI 应用进行自动化对抗测试。
- 通过组合**数据集 / 转换器 / 执行器 / 评分器**完成单轮攻击测试，并支持预设场景（OWASP LLM Top10、Jailbreak Pack 等）。
- 前端提供"表单驱动 + 预设场景为主"的低代码作者体验，YAML 双向同步以满足高级用户。
- 通过 Python entry-points 让高级用户注册自定义插件（target/converter/executor/scorer/scenario）。

**MVP 不包含**：多轮/带反馈的执行器、NL→测试配置、人工测试与重放、SaaS 多租户、运行控制（取消/暂停/续跑）。这些进入 P1/P2，后续单独立项。

---

## 2. 设计决策摘要

| 维度 | 选择 |
|---|---|
| 后端语言 | Python 3.11+ |
| Web 框架 | FastAPI（单进程） |
| 并发 | asyncio + Semaphore，**不**引入 Celery/RQ |
| 关系存储 | SQLAlchemy 2.x + Alembic；本地 SQLite，部署 Postgres |
| 大对象存储 | 抽象 `BlobStore`（默认本地 FS，可换 S3 兼容） |
| 凭证 | `cryptography.fernet`，master key 从 `AIREDTEAM_MASTER_KEY` 读取 |
| 认证（MVP） | 单管理员密码（`.env`）+ httpOnly cookie |
| 实时进度 | SSE（`/runs/{id}/events`） |
| 配置契约 | RunSpec YAML（JSON Schema 校验） |
| 插件机制 | Python entry-points（`airedteam.targets/.converters/...`） |
| 前端 | React 18 + TS + Vite + shadcn/ui + TanStack Query + Monaco + Recharts |
| 部署 | Docker 多阶段镜像 + docker-compose（app + postgres） |

---

## 3. 整体架构

```
┌────────────────────────────────────────────────────────┐
│  React + Vite + shadcn/ui (SPA)                        │
│  目标配置 / 行动配置 / 结果查询 / 简易报告              │
└──────────────────┬─────────────────────────────────────┘
                   │ REST (JSON) + SSE
┌──────────────────▼─────────────────────────────────────┐
│  FastAPI 单进程                                         │
│   HTTP Router → Application Services → Domain core      │
│   ↓                                                     │
│   Plugin Registry (entry-points)                        │
│   Async Run Engine (asyncio + Semaphore)                │
│   Storage (SQLAlchemy) + BlobStore + SecretBox          │
└────────────────────────────────────────────────────────┘
```

**进程模型**：单 FastAPI 进程；run 在 asyncio event loop 中作为后台 task 运行（`asyncio.create_task` 提交到进程内 RunEngine，由它管理 Semaphore 并流式写库）。

**存储双栈**：
- 关系型 DB：所有结构化元数据（targets/datasets[meta]/runs/attempts/scores/users/secrets）。
- BlobStore：dataset 原始内容（JSONL）、conversation 全量、长 response、judge raw output。DB 仅存指针 + sha256。

**配置统一性**：前端表单 / 预设场景 / NL→配置（P2）最终都产出**同一个 RunSpec YAML**，后端只认 RunSpec。这保证表单和 YAML 100% 互通。

---

## 4. 核心抽象

7 个核心抽象，全部为 Python `Protocol`/ABC，通过 entry-points 注册到全局 `Registry`：

| 抽象 | 职责 | 关键接口 |
|---|---|---|
| **Target** | 被测 AI 应用 / judge 模型，统一聊天接口 | `async send(conversation: Conversation) -> Response` |
| **Dataset** | 测试样本来源 | `async load() -> AsyncIterator[Sample]`；`fingerprint() -> str` |
| **Converter** | 对 prompt 做变换，可链式 | `async convert(text: str, ctx) -> str` |
| **Executor** | 单次"攻击交互"的工作流（MVP 仅 `SingleTurnExecutor`） | `async execute(target, sample, converters, scorers, ctx) -> Attempt` |
| **Scorer** | 对 Attempt 打分 | `async score(attempt) -> list[Score]` |
| **Orchestrator** | 把 dataset × converters × targets × executor × scorers 串起来跑一个 Run | `async run(spec: RunSpec) -> RunHandle` |
| **Preset Scenario** | RunSpec 工厂 + 参数 schema | `build(params: dict) -> RunSpec` |

**核心数据结构**（pydantic）：

- `Sample{id, input: str, metadata: dict, expected: any | None, category: str | None}`
- `Conversation = list[Message{role, content}]`
- `Attempt{id, run_id, target_id, sample_id, conversation, original_prompt, converted_prompt, response, converters_applied: list[str], started_at, finished_at, latency_ms, token_usage, error | None}`
- `Score{attempt_id, scorer_id, value: JSON, value_type: 'bool'|'float'|'category', rationale, raw_blob_path | None}`
- `Run{id, name, spec_yaml, status, created_by, started_at, finished_at, summary_stats}`

**插件契约**：每个插件类暴露 `name: str`、`schema: pydantic.BaseModel`（其字段决定前端表单）、`async create(params) -> Instance`。`GET /api/v1/registry` 把 `schema` 导出为 JSON Schema 给前端动态渲染表单。

**entry-points 示例**：

```toml
[project.entry-points."airedteam.targets"]
openai_compatible = "airedteam.builtins.targets:OpenAICompatibleTarget"
anthropic_compatible = "airedteam.builtins.targets:AnthropicCompatibleTarget"

[project.entry-points."airedteam.converters"]
base64 = "airedteam.builtins.converters:Base64Converter"
rot13 = "airedteam.builtins.converters:Rot13Converter"
template = "airedteam.builtins.converters:TemplateConverter"
translate = "airedteam.builtins.converters:TranslateConverter"

[project.entry-points."airedteam.datasets"]
huggingface = "airedteam.builtins.datasets:HuggingFaceDataset"
local_jsonl = "airedteam.builtins.datasets:LocalJsonlDataset"

[project.entry-points."airedteam.executors"]
single_turn = "airedteam.builtins.executors:SingleTurnExecutor"

[project.entry-points."airedteam.scorers"]
regex_refusal = "airedteam.builtins.scorers:RegexRefusalScorer"
keyword = "airedteam.builtins.scorers:KeywordScorer"
llm_judge = "airedteam.builtins.scorers:LlmJudgeScorer"

[project.entry-points."airedteam.scenarios"]
owasp_llm_top10 = "airedteam.builtins.scenarios:OwaspLlmTop10"
jailbreak_pack = "airedteam.builtins.scenarios:JailbreakPack"
```

---

## 5. RunSpec 格式

YAML 为主（后端同时接受 JSON），用 JSON Schema 校验。`targets` 始终为数组（单 target 即长度 1，多 target 用于横向对比，简化解析）。每个 target 项可以是已入库记录的 `config_id`，也可以 `inline` 临时定义不入库。`dataset` 同样支持 `inline`。

```yaml
version: 1
name: "owasp-llm01-demo"

# 二选一：单 target 或 targets 数组（横向对比）
targets:
  - { ref: "openai_compatible", config_id: 42 }
  - { ref: "anthropic_compatible",
      inline: { base_url: "https://...", model: "claude-3-5", api_key_secret_id: 9 } }

dataset:
  ref: "huggingface"
  params: { repo: "walledai/AdvBench", split: "train", limit: 100 }
  # 或：inline: { samples: [{input: "..."}, ...] }  # 不入库即用

converters:                   # 顺序应用；空数组 = 不变换
  - { ref: "base64",  params: {} }
  - { ref: "translate", params: { target_lang: "zh" } }

executor:
  ref: "single_turn"
  params: { system_prompt: null }

scorers:
  - { ref: "regex_refusal", params: { patterns: ["I can'?t help"] } }
  - { ref: "llm_judge",     params: { judge_target_id: 7, rubric: "harmful_content_v1" } }

concurrency: { max_in_flight: 16 }
sampling:    { seed: 1234, shuffle: false }
```

---

## 6. Run 生命周期 & 数据流

```
POST /runs (RunSpec)
  → 校验 (JSON Schema + Registry dry-run 实例化所有 ref)
  → 创建 Run(status=pending) → 提交到 RunEngine

RunEngine.start(run):
  1. dataset.load() → 物化 Sample 列表 → 写入 attempts(status=queued)
     大数据集流式 load + 分批写库，避免内存峰值
  2. asyncio.Semaphore(max_in_flight)
  3. 笛卡尔积 (sample × target)，对每对起一个 task：
       - converters 链式应用 → converted_prompt
       - executor.execute(target, sample, ...) → Attempt
       - scorers 并行打分 → list[Score]
       - 单个 attempt 完成立即 INSERT(attempt+scores)
       - SSE 发布 attempt.completed
  4. 全部完成 → 计算 summary_stats（pass_rate、by_target、by_converter、
     by_category、by_scorer）→ 更新 Run(status=finished)

错误处理：单个 attempt 异常仅标记 attempt.error，不中断 Run；
          整个 run 异常（如 dataset 加载失败）→ status=failed，记录 error。
```

**SSE 事件类型**：`attempt.started` / `attempt.completed` / `run.progress`（节流到每秒一次）/ `run.finished` / `run.failed`。

---

## 7. 存储 Schema

### 关系型表

```
users(id, name, password_hash, role, created_at)

secrets(id, name, ciphertext, created_by, created_at)
  -- ciphertext = Fernet(master_key).encrypt(plaintext)

targets(id, name, type, config_json, secret_ref, created_by, created_at)

datasets(id, name, source_type, source_ref, fingerprint, blob_path,
         sample_count, schema_version, created_at)
  -- blob_path 指向 JSONL；fingerprint = sha256(blob)

scenarios_presets(id, name, version, builder_module, params_schema_json)
  -- 系统内置 + 未来用户自定义

runs(id, name, spec_yaml, status, created_by, started_at, finished_at,
     summary_stats_json, dataset_id NULL)
  -- 多 target 通过 attempts.target_id 关联；不在 runs 上保存"主 target"
  -- status: pending | running | finished | failed

attempts(id, run_id, target_id, sample_id, status,
         original_prompt, converted_prompt,
         response_inline TEXT NULL,           -- ≤8KB inline
         response_blob_path TEXT NULL,        -- >8KB spill
         conversation_blob_path TEXT NULL,    -- 多轮预留
         converters_applied_json,
         started_at, finished_at, latency_ms, token_usage_json,
         error TEXT NULL)

scores(id, attempt_id, scorer_ref, value_type,
       value JSONB,                           -- bool/float/category 统一
       rationale TEXT NULL,
       raw_blob_path TEXT NULL)               -- judge LLM 原始输出 spill

audit_log(id, user_id, action, target_type, target_id, payload_json, ts)
```

**索引**：`attempts(run_id, status)`、`attempts(run_id, target_id)`、`scores(attempt_id)`、`runs(status, started_at desc)`。

### BlobStore 抽象

```python
class BlobStore(Protocol):
    async def put(self, content: bytes) -> str: ...   # 返回 path
    async def get(self, path: str) -> bytes: ...
    async def delete(self, path: str) -> None: ...
```

默认实现：`LocalBlobStore`，路径 `./data/blobs/{sha256[:2]}/{sha256}`，内容寻址，自动去重。

### Secret 处理规则

- master key 从 `AIREDTEAM_MASTER_KEY` env var 读取，缺失则启动失败。
- 入库前 Fernet 加密；调用 target 的瞬间解密，不持久化明文到任何日志。
- API 永远不返回 secret 的明文，只返回 `{id, name, created_at}`。

---

## 8. HTTP API（v1）

约定：所有路由 `/api/v1/`，JSON in/out，错误统一 `{error:{code, message, details}}`，分页 `?page=&page_size=`。

```
# 注册表（动态 UI 渲染依赖它）
GET  /registry
   → { targets:[{name, description, params_schema}], converters:[…],
       datasets:[…], executors:[…], scorers:[…], scenarios:[…] }

# 凭证
POST /secrets               { name, value }   → 仅返回 {id, name}
GET  /secrets               → list（不含 value）
DELETE /secrets/{id}

# Targets
POST /targets               { name, type, config, secret_id? }
GET /targets[/{id}]
PATCH /targets/{id}
DELETE /targets/{id}
POST /targets/{id}:test     → 发一条 ping，返回连通性 + 模型回复

# Datasets
POST /datasets:from_huggingface  { repo, split, limit, name } → 异步 ingest job
POST /datasets:from_upload (multipart, .json/.jsonl)         → 同步入库
GET  /datasets[/{id}]
DELETE /datasets/{id}
GET  /datasets/{id}/preview?n=20

# Scenarios (presets)
GET  /scenarios
POST /scenarios/{name}:render  { params } → RunSpec YAML（不执行，仅渲染给 UI）

# Runs
POST /runs                  body: RunSpec YAML 或 JSON → 校验+创建+异步启动
GET  /runs?status=&page=
GET  /runs/{id}             → 含 summary_stats
GET  /runs/{id}/attempts?scorer=&pass=&target=&page=
GET  /runs/{id}/events      → text/event-stream
DELETE /runs/{id}           MVP: 仅删记录，不支持取消

# 报告
GET  /runs/{id}/report      → 聚合数据（pass_rate by_target/converter/category/scorer）

# 认证（MVP：单管理员密码）
POST /auth/login            { password } → set httpOnly cookie
POST /auth/logout
GET  /auth/me
```

---

## 9. 前端 MVP

### 技术栈

React 18 + TypeScript + Vite + shadcn/ui + TanStack Query + React Router + Monaco（YAML 编辑器）+ react-hook-form + zod + `@rjsf/core`（JSON Schema → 表单）+ Recharts + 原生 EventSource。

### 路由

```
/login                    单管理员密码登录
/targets                  列表 + "新建/编辑/测试连接" 抽屉
/secrets                  列表 + 新建（value 一次性）
/datasets                 列表 + "从 HF 拉取" / "上传 JSON" / 预览
/runs                     Run 列表 + 状态徽标 + 进度条
/runs/new                 ⭐ 行动配置主入口
/runs/{id}                Run 详情：概览 / 明细 / 图表 三标签
```

### `/runs/new` 核心 UX

顶部 Tab 切换两条路径，**底层都生成同一 RunSpec**，左表单 / 右 YAML 实时双向同步：

- **预设场景 Tab**：场景下拉（OWASP LLM01…）→ 按场景 schema 渲染参数表单 → 选 target → 渲染 RunSpec 到右侧。
- **自定义 Tab**：分层选择 ① Targets（多选）② Dataset ③ Converters（拖拽排序）④ Executor ⑤ Scorers（多选）⑥ Concurrency/Sampling。
- **YAML 编辑器**：用户直接编辑反向同步表单；schema 错误下划线提示。
- **底部按钮**：[校验]、[试运行 5 条]（创建临时 Run，limit=5）、[启动 Run]。

**所有动态表单都由 `/registry` 返回的 JSON Schema 驱动**，新增插件时前端零改动自动获得新表单。

### Run 详情

- **概览 Tab**：summary_stats（总样本数、通过率、错误率、平均延迟），多 target 时并排显示。
- **明细 Tab**：虚拟滚动表格（列：sample_id / converter chain / converted_prompt / response / scores 徽标 / 状态 / target）。点击行打开侧抽屉显示完整 conversation。多 target 支持按 target 筛选。
- **图表 Tab**：Recharts 条形图，按 converter / category / scorer / target 维度的通过率分组。
- **实时进度**：SSE 驱动顶部进度条 + "已完成 / 总数 / 失败"。

---

## 10. 项目结构

```
airedteam/
├── pyproject.toml
├── airedteam/
│   ├── core/               # 抽象（protocols、dataclass、Registry、SecretBox、BlobStore 接口）
│   ├── engine/             # RunEngine、SSE EventBus、Concurrency
│   ├── storage/            # SQLAlchemy models、Alembic migrations、blob 实现
│   ├── builtins/
│   │   ├── targets/
│   │   ├── datasets/
│   │   ├── converters/
│   │   ├── executors/
│   │   ├── scorers/
│   │   └── scenarios/
│   ├── api/                # FastAPI routers + pydantic I/O schemas
│   ├── services/           # 应用服务（run_service、target_service…）
│   ├── runspec/            # RunSpec pydantic 模型 + YAML 解析 + JSON Schema 导出
│   └── cli.py              # `airedteam serve`、`airedteam run path/to/spec.yaml`
├── frontend/               # Vite + React，构建产物由 FastAPI 静态托管
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docker/Dockerfile       # 多阶段：node 构建前端 → python 拷静态 + 安依赖
└── docker-compose.yml      # app + postgres + 命名 volume 挂 ./data/blobs
```

---

## 11. 测试策略

- **TDD**：每层抽象先写契约测试（pytest + pytest-asyncio）。
- **每个内置插件**：1 个 unit 测试 + 1 个最小集成测试。
- **端到端 happy path**：`EchoTarget`（直接 echo prompt）+ inline 3 条 dataset，跑完整 run，断言：
  - attempts × scores 写库正确；
  - summary_stats 计算正确；
  - SSE 事件序列符合预期；
  - blob 寻址命中。
- **API 层**：FastAPI `TestClient`，覆盖鉴权/校验失败路径。
- **前端 MVP**：vitest 覆盖 schema-to-form、RunSpec 序列化反序列化、SSE hook；不强制 e2e。

---

## 12. 部署

- 多阶段 Dockerfile：node 构建前端 → python 安装依赖并复制前端构建产物。
- `docker-compose.yml`：`app` + `postgres`，命名 volume 挂 `./data/blobs`。
- 启动需提供 env：`AIREDTEAM_MASTER_KEY`、`AIREDTEAM_ADMIN_PASSWORD`、`DATABASE_URL`。
- `airedteam serve` 单命令启动 FastAPI（uvicorn）。

---

## 13. 边界与延后项

**显式不在 MVP 范围**：
- 多轮 / 带反馈攻击执行器
- 运行控制（取消 / 暂停 / 续跑 / 重试）
- NL → 测试配置
- 人工测试与重放
- 多用户 / RBAC（MVP 仅单管理员）
- 外部密钥管理（Vault/SM）
- 移动端/PC AI 应用接入、AI Agent target
- PDF 报告导出

**预留扩展点**：
- `Executor` 抽象天然支持多轮（`Conversation` 已是 list）。
- `attempts.conversation_blob_path` 字段已预留。
- `BlobStore` 抽象可换 S3。
- `Target` 抽象可加移动端/Agent 适配器。
- entry-points 已分组到位，加新组（如 `airedteam.report_renderers`）即可。

---

## 14. 主要风险

| 风险 | 缓解 |
|---|---|
| HuggingFace 拉取慢/失败 | 拉取作为异步 ingest job；失败保留状态供重试；本地 BlobStore 缓存 |
| 大 run 内存峰值 | dataset 流式 load + 分批写库；attempt 完成立即落库不堆积 |
| LLM judge 成本高 | scorer 配置层支持采样比（仅对 X% attempts 用 judge）—— 在 scorer params 中承接 |
| Master key 泄漏 | 启动时校验 key 长度 + 从 env 读取，不允许命令行参数；secret 永不返回前端 |
| asyncio 单进程吞吐天花板 | MVP 接受；P1 评估是否升级到 Celery/RQ |
| Schema 演化 | 关系型用 Alembic；RunSpec 含 `version` 字段，后端按版本路由解析 |
