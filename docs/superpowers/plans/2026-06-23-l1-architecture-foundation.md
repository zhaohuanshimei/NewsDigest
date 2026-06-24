# News Digest V2 L1-A Architecture Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the V2 architecture document set that defines system boundaries, domain language, API resource model, contract strategy, and non-functional targets for all later implementation work.

**Architecture:** This phase is documentation-first. It creates a stable design spine in `docs/architecture/` before any API or Web runtime code is written, and keeps `claude.md`, the master plan, and architecture docs aligned so parallel workers can implement later tasks without redefining the system each time.

**Tech Stack:** Markdown, repository docs in `docs/`, root guidance in `claude.md`, V2 master plan in `docs/superpowers/plans/2026-06-23-news-digest-v2-master-plan.md`

## Global Constraints

- Scope is limited to `L1-A01` through `L1-A05`; do not start `L1-B` code scaffolding inside this plan.
- All runtime coupling must be API-first; the frontend must not read backend export files directly.
- Shared contracts must live in `packages/shared-types`; reusable UI primitives and design tokens must live in `packages/ui`.
- Documentation is a first-class deliverable; `claude.md`, `docs/architecture/`, and the master plan must stay consistent.
- All outputs must be written in clear Chinese so the repository guidance remains locally coherent.
- Each task must end with a verifiable documentation artifact and a clean git checkpoint.

---

### Task 1: 建立架构总纲与目录索引

**Files:**
- Modify: `docs/architecture/README.md`
- Create: `docs/architecture/overview.md`

**Interfaces:**
- Consumes: `claude.md` architecture principles, `docs/superpowers/plans/2026-06-23-news-digest-v2-master-plan.md`
- Produces: `docs/architecture/overview.md` as the system boundary source; `docs/architecture/README.md` as the architecture doc index

- [ ] **Step 1: 写出目录索引需要的最小失败校验**

```markdown
# Architecture Docs

- `overview.md`
- `domain-model.md`
- `api-boundary.md`
- `contract-strategy.md`
- `non-functional-targets.md`
```

- [ ] **Step 2: 运行检查，确认当前文档缺失**

Run: `test -f docs/architecture/overview.md && echo "exists" || echo "missing"`
Expected: `missing`

- [ ] **Step 3: 写入 `overview.md` 初稿**

```markdown
# V2 架构总览

## 目标
- V2 是一个前后端分离、API-first 的 News Digest 系统。
- Web 只是首发客户端，后续需要支持更多客户端形态。

## 模块边界
- `services/api`：对外 API、内容读取、调度入口、后台能力承载点。
- `apps/web`：首发 Web 客户端，只通过 HTTP/API 契约消费内容。
- `packages/shared-types`：共享资源模型、响应 schema、类型生成结果。
- `packages/ui`：设计 token 与可复用界面基础组件。
- `docs/context`：V1 提炼出的只读背景知识。

## 核心原则
- 前端不得直接读取后端导出 JSON 文件。
- 后端输出以 API 为第一形态，不以静态导出文件为主接口。
- V1 能力只能提炼思路，不直接照搬结构。
```

- [ ] **Step 4: 更新 `README.md` 作为架构文档入口**

```markdown
# Architecture Docs

V2 架构文档索引：

- `overview.md`：系统目标、边界与模块关系
- `domain-model.md`：核心实体、状态与关系
- `api-boundary.md`：首发 API 资源模型与错误格式
- `contract-strategy.md`：shared-types 与 schema 演进规则
- `non-functional-targets.md`：性能、SEO、稳定性与可访问性目标
```

- [ ] **Step 5: 运行检查确认文件存在且标题正确**

Run: `grep -E '^# ' docs/architecture/overview.md docs/architecture/README.md`
Expected: output contains `# V2 架构总览` and `# Architecture Docs`

- [ ] **Step 6: 提交**

```bash
git add docs/architecture/README.md docs/architecture/overview.md
git commit -m "docs(L1-A01): add v2 architecture overview"
```

### Task 2: 固化领域模型与统一术语

**Files:**
- Create: `docs/architecture/domain-model.md`

**Interfaces:**
- Consumes: `docs/architecture/overview.md`, `docs/context/VERIFY_DB.md`, `docs/context/DEVELOPMENT_PLAN.md`
- Produces: canonical domain names for `Source`, `Article`, `Cluster`, `Digest`, `Translation`

- [ ] **Step 1: 先确认领域模型文档不存在**

Run: `test -f docs/architecture/domain-model.md && echo "exists" || echo "missing"`
Expected: `missing`

- [ ] **Step 2: 写入领域模型文档**

```markdown
# V2 领域模型

## 核心实体

### Source
- 表示一个内容源。
- 关键字段：`id`, `name`, `kind`, `language`, `enabled`, `fetch_strategy`

### Article
- 表示一次抓取后得到的标准化文章。
- 关键字段：`id`, `source_id`, `url`, `title`, `summary`, `body`, `published_at`, `language`

### Cluster
- 表示同一新闻事件的聚合结果。
- 关键字段：`id`, `representative_article_id`, `size`, `first_seen_at`, `score`

### Digest
- 表示某个发布日期对外展示的精选集合。
- 关键字段：`date`, `entries`, `rank`, `category`, `published_at`

### Translation
- 表示针对 `Article` 或 `DigestEntry` 的翻译结果。
- 关键字段：`id`, `target_language`, `translated_title`, `translated_summary`, `provider`, `status`

## 关系
- `Source -> Article`：一个源可产生多篇文章。
- `Article -> Cluster`：多篇文章可归入一个事件聚类。
- `Cluster -> Digest`：一个日报由多个聚类条目组成。
- `Article/DigestEntry -> Translation`：原始内容可衍生多种语言翻译。

## 统一术语
- 对外使用“日报”对应 `Digest`
- 对外使用“事件”对应 `Cluster`
- 对外使用“来源”对应 `Source`
- 不再混用 `export`, `feed item`, `post` 作为核心模型名
```

- [ ] **Step 3: 运行最小一致性检查**

Run: `grep -E '^### (Source|Article|Cluster|Digest|Translation)$' docs/architecture/domain-model.md | wc -l`
Expected: `5`

- [ ] **Step 4: 检查链路是否完整**

Run: `grep 'Source -> Article' docs/architecture/domain-model.md && grep 'Cluster -> Digest' docs/architecture/domain-model.md`
Expected: both lines found

- [ ] **Step 5: 提交**

```bash
git add docs/architecture/domain-model.md
git commit -m "docs(L1-A02): define v2 domain model"
```

### Task 3: 定义首发 API 边界

**Files:**
- Create: `docs/architecture/api-boundary.md`

**Interfaces:**
- Consumes: `docs/architecture/overview.md`, `docs/architecture/domain-model.md`, `packages/shared-types/README.md`
- Produces: stable first-release API route set and response/error model

- [ ] **Step 1: 验证 API 边界文档尚未创建**

Run: `test -f docs/architecture/api-boundary.md && echo "exists" || echo "missing"`
Expected: `missing`

- [ ] **Step 2: 写入 API 资源模型**

```markdown
# V2 API 边界

## 首发路由
- `GET /api/v1/digests/latest`
- `GET /api/v1/digests/{date}`
- `GET /api/v1/archive/dates`
- `GET /api/v1/clusters/{id}`
- `GET /api/v1/articles/{id}`
- `GET /api/v1/health`

## 响应原则
- 所有公开读取接口返回可被 `packages/shared-types` 表达的稳定对象。
- Web 端消费的是 API 资源，不是数据库行结构。
- 未找到资源时优先返回 `404` 与统一错误对象。

## 错误格式
```json
{
  "error": {
    "code": "digest_not_found",
    "message": "未找到指定日期的日报",
    "request_id": "req_123"
  }
}
```

## 首发不纳入范围
- 后台写接口
- 认证与权限模型
- 复杂筛选、搜索建议、多语言偏好写入
```

- [ ] **Step 3: 校验首发路由覆盖**

Run: `grep -E '^- `GET /api/v1/' docs/architecture/api-boundary.md | wc -l`
Expected: `6`

- [ ] **Step 4: 校验错误模型存在**

Run: `grep '"code": "digest_not_found"' docs/architecture/api-boundary.md`
Expected: matching line found

- [ ] **Step 5: 提交**

```bash
git add docs/architecture/api-boundary.md
git commit -m "docs(L1-A03): define v2 api boundary"
```

### Task 4: 定义 shared-types 契约策略

**Files:**
- Create: `docs/architecture/contract-strategy.md`

**Interfaces:**
- Consumes: `docs/architecture/api-boundary.md`, `packages/shared-types/README.md`
- Produces: contract lifecycle rules for API schema and Web consumption

- [ ] **Step 1: 验证契约策略文档不存在**

Run: `test -f docs/architecture/contract-strategy.md && echo "exists" || echo "missing"`
Expected: `missing`

- [ ] **Step 2: 写入契约策略**

```markdown
# V2 契约策略

## 契约来源
- API schema 是共享契约的单一事实来源。
- `packages/shared-types` 负责沉淀对外资源模型和类型导出。

## 同步规则
1. 先更新 API 资源定义。
2. 再更新 `packages/shared-types`。
3. 最后更新 Web 与 API 实现。

## 兼容性规则
- 新增可选字段属于非破坏性变更。
- 删除字段、修改字段语义、修改错误结构属于 breaking change。
- breaking change 必须在文档中明确记录并提升版本。

## 禁止事项
- 前端私自定义与 API 不一致的资源名称。
- 直接把数据库表字段暴露为公共契约。
```

- [ ] **Step 3: 运行关键字检查**

Run: `grep -E 'API schema|packages/shared-types|breaking change' docs/architecture/contract-strategy.md`
Expected: all three concepts appear

- [ ] **Step 4: 提交**

```bash
git add docs/architecture/contract-strategy.md
git commit -m "docs(L1-A04): define shared contract strategy"
```

### Task 5: 定义非功能目标并同步总纲

**Files:**
- Create: `docs/architecture/non-functional-targets.md`
- Modify: `claude.md`

**Interfaces:**
- Consumes: `docs/design/DESIGN_DIRECTIONS.md`, `docs/superpowers/plans/2026-06-23-news-digest-v2-master-plan.md`
- Produces: measurable non-functional targets linked from root guidance

- [ ] **Step 1: 验证非功能目标文档不存在**

Run: `test -f docs/architecture/non-functional-targets.md && echo "exists" || echo "missing"`
Expected: `missing`

- [ ] **Step 2: 写入目标文档**

```markdown
# V2 非功能目标

## 性能
- 首发关键页面移动端 Lighthouse Performance >= 90
- 关键页面首屏内容优先，避免无必要运行时依赖

## 可访问性
- Lighthouse Accessibility >= 95
- 交互控件触达尺寸 >= 44px
- 键盘焦点、对比度和语义结构必须可验证

## SEO
- 首页、归档、详情页均具备完整 meta
- 提供 `robots.txt`、`sitemap.xml`、基础结构化数据

## 稳定性
- API 需区分 liveness 与 readiness
- 每日内容更新失败必须可被监控发现

## 内容质量
- 翻译、聚类、排序失败不得静默污染公开结果
- 对外展示内容必须具备可追踪来源
```

- [ ] **Step 3: 在 `claude.md` 中挂载架构文档组**

```markdown
## Source Of Truth

- Architecture docs: `docs/architecture/`
- Master development plan: `docs/superpowers/plans/2026-06-23-news-digest-v2-master-plan.md`
```

- [ ] **Step 4: 运行文档一致性检查**

Run: `grep 'docs/architecture/' claude.md && grep 'Lighthouse Accessibility >= 95' docs/architecture/non-functional-targets.md`
Expected: both lines found

- [ ] **Step 5: 提交**

```bash
git add docs/architecture/non-functional-targets.md claude.md
git commit -m "docs(L1-A05): define non-functional targets"
```

---

## Self-Review

- **Spec coverage:** This plan covers `L1-A01` through `L1-A05` from the V2 master plan and does not drift into `L1-B` runtime scaffolding.
- **Placeholder scan:** No `TODO`, `TBD`, or unresolved file targets remain.
- **Type consistency:** Domain names, API route names, and `packages/shared-types` references stay consistent across all tasks.

---

**Plan complete and saved to `docs/superpowers/plans/2026-06-23-l1-architecture-foundation.md`. Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints

**Which approach?**
