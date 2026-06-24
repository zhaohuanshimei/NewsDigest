# L1-B Minimal Shared Types + API Design

> Status: approved for planning
> Scope: `packages/shared-types` + `services/api`
> Date: 2026-06-24

## Goal

将 News Digest V2 从“仅有架构文档”推进到“存在真实可运行代码骨架”的第一步，建立一个最小但完整的 `shared-types + api` 闭环。

这轮工作的目标不是交付业务功能，而是验证以下三件事：

- `packages/shared-types` 可以成为真实的公共契约层，而不是占位目录
- `services/api` 可以以最小 FastAPI 服务形式启动并暴露健康检查接口
- API 返回结构与共享契约在语义上保持一致，为后续 `digest/archive/detail` 扩展提供稳定起点

## Problem

当前仓库已经完成 `L1-A` 架构文档基线，但 `apps/web`、`services/api`、`packages/shared-types`、`packages/ui` 仍然是占位目录。若直接进入数据库、抓取、digest 读取或前端页面实现，会在没有运行时骨架和公共契约的情况下推进，导致边界漂移、命名不一致、实现顺序混乱。

因此，`L1-B` 的首个子项目必须先证明：

- V2 的 `API-first` 架构不是纸面设计
- 前后端共享契约有明确落点
- 后续读取型资源可以沿同一结构扩展，而不需要返工基础目录和命名体系

## Research Decision

本轮在 API 设计风格上采用 `Adapt` 策略，而不是完整采用某个现成规范或完全手写一套新风格。

### Candidates Considered

- `JSON:API`
- `Zalando RESTful API Guidelines`
- `Microsoft REST API Guidelines`
- `FastAPI + OpenAPI`

### Decision

采用以下组合：

- 使用 `FastAPI + OpenAPI-first` 作为契约承载和文档发布方式
- 使用轻量 REST 资源式 URL
- 吸收 `Zalando` / `Microsoft` 关于 API-first、URL 一致性、错误模型、版本治理的原则
- 只借鉴 `JSON:API` 的资源对象与统一错误建模思想，不采用其完整 envelope、media type 和 relationship 体系

### Why This Wins

- 符合当前项目已经明确的 `API-first` 约束
- 与 `FastAPI` 的默认 OpenAPI 能力天然对齐
- 不会把首发只读内容 API 过早做成“超通用规范驱动 API”
- 保留后续演进到更严格契约导出流程的空间

## Scope

### In Scope

- 将 `packages/shared-types` 从 README 占位目录升级为真实可导出的类型包
- 定义最小共享资源：
  - `HealthResource`
  - `ApiError`
- 在 `services/api` 中建立最小 FastAPI 骨架
- 实现 `GET /api/v1/health`
- 让 API 的公开响应与共享契约语义一致
- 提供最小 smoke test 或等价验证机制
- 确保 `/openapi.json` 与 `/docs` 可用

### Out of Scope

- 数据库与 Alembic
- 抓取、正文抽取、规范化、聚类、digest 生成、翻译
- `GET /api/v1/digests/*`、`/archive/*`、`/clusters/*`、`/articles/*` 的真实业务实现
- `apps/web` 与 `packages/ui` 的运行时代码
- 重型 schema 生成链或自动 SDK 生成
- 复杂全局异常体系、权限体系、后台写接口

## Architecture

### High-Level Shape

本轮只建立两个最小模块：

- `packages/shared-types`
- `services/api`

它们形成单向依赖关系：

- `shared-types` 定义公开资源的命名与外形
- `api` 负责通过 HTTP 提供这些资源

这轮不要求 `shared-types` 被 API 在运行时直接强依赖到“同一份对象实现”，但要求：

- 命名一致
- 字段语义一致
- OpenAPI 结构与共享契约保持同一公共语言

### Design Principle

- 优先验证边界，不优先追求自动生成
- 先建立最小真实契约，再引入更复杂的 schema/export/tooling
- 目录可以为未来扩展预留位置，但只实现最小必要文件

## Module Design

### `packages/shared-types`

职责：

- 作为公开资源契约的唯一共享入口
- 沉淀 Web 与 API 都认可的对外资源名
- 严格避免放入数据库表类型、ORM 类型、内部 service 类型

建议结构：

```text
packages/shared-types/
  README.md
  src/
    index.ts
    resources/
      health.ts
      error.ts
```

这轮至少导出：

- `HealthResource`
- `ApiError`

这轮可以保留未来资源的导出位或注释性说明，但不要求完整实现：

- `DigestResource`
- `DigestEntryResource`
- `ArchiveDateListResource`
- `ClusterDetailResource`
- `ArticleDetailResource`

### `services/api`

职责：

- 提供最小可启动的 FastAPI 应用
- 暴露版本化前缀下的健康检查接口
- 建立后续扩展所需的目录边界

建议结构：

```text
services/api/
  README.md
  app/
    main.py
    core/
      config.py
      metadata.py
    routers/
      health.py
    schemas/
      health.py
      error.py
    services/
    repositories/
```

说明：

- `services/` 与 `repositories/` 这轮可以为空目录或用占位文件说明职责
- 这轮只真正实现 `main.py`、`routers/health.py` 与最小 schema 文件

## API Design

### Route

- `GET /api/v1/health`

### Response

`200 OK` 返回 `HealthResource` 语义对象。

建议字段：

- `status`: 服务状态，首发固定使用简单稳定值，如 `ok`
- `service`: 服务名，明确该接口属于 `news-digest-api`
- `version`: 当前 API 或应用版本字符串

示例：

```json
{
  "status": "ok",
  "service": "news-digest-api",
  "version": "0.1.0"
}
```

### Error Model

本轮建立统一错误对象，但只做到最小值。

`ApiError` 建议字段：

- `code`
- `message`
- `request_id`

说明：

- `request_id` 即使当前先用简单占位值，也必须保留字段位
- 本轮不强制建立复杂全局异常处理中间件
- 已知错误与未来业务错误均应向该公共错误模型靠拢

示例：

```json
{
  "error": {
    "code": "service_unavailable",
    "message": "服务暂时不可用",
    "request_id": "req_placeholder"
  }
}
```

## Contract Strategy For This Phase

本轮不引入重型契约生成链，采用“轻契约一致性”策略：

- `shared-types` 负责定义公共资源名与字段语义
- `services/api` 的 Pydantic/FastAPI response model 负责生成 OpenAPI
- 两者通过同名资源、同义字段和文档约束保持一致

这意味着本轮的重点是：

- 先把命名体系固定住
- 先把目录与契约入口做真实
- 后续在 `L1-D05` 再演进为更严格的契约导出与消费机制

## Testing And Verification

本轮测试只覆盖最小链路：

- API 应用可启动
- `GET /api/v1/health` 返回 `200`
- 返回 JSON 至少包含 `status`、`service`、`version`
- `/openapi.json` 可访问

如果本轮引入测试文件，优先选择：

- API smoke test
- 单一路由断言

不要求：

- 覆盖数据库相关测试
- 覆盖复杂错误路径矩阵
- 覆盖端到端前后端联调

## Acceptance Criteria

完成本轮后，以下条件必须同时成立：

- `packages/shared-types` 不再只是 README 占位目录
- 存在清晰的 `src/index.ts` 导出入口
- `HealthResource` 与 `ApiError` 已定义
- `services/api` 可在本地启动
- `GET /api/v1/health` 可访问并返回稳定 JSON
- FastAPI 文档页或 OpenAPI JSON 可见
- 目录结构足以承接后续 `digest/archive/detail` 读取型接口

## Follow-On Work

本轮完成后，后续最自然的推进顺序是：

1. 在 `packages/shared-types` 扩展：
   - `DigestResource`
   - `ArchiveDateListResource`
   - `ClusterDetailResource`
   - `ArticleDetailResource`
2. 在 `services/api` 中增加：
   - `GET /api/v1/digests/latest`
   - `GET /api/v1/digests/{date}`
   - `GET /api/v1/archive/dates`
3. 再考虑 `apps/web` 如何消费这些资源

## Risks And Guardrails

### Risks

- 过早把本轮扩展成完整业务 API，导致首个子项目失焦
- 过早引入 codegen 或 SDK 生成，使问题从“边界清不清楚”转移到“工具链顺不顺”
- 把内部实现结构误暴露成公共契约

### Guardrails

- 本轮只做 `health`
- 公共契约只围绕公开资源名，不围绕数据库结构
- 不因为“顺手”而启动 digest、archive、DB 或 Web 代码
- 如果需要新字段，先更新契约设计，再更新 API 实现

## Implementation Recommendation

实现阶段采用以下顺序最稳妥：

1. 初始化 `packages/shared-types` 的真实文件结构
2. 定义 `HealthResource` 与 `ApiError`
3. 初始化 `services/api` 的 FastAPI 应用入口
4. 实现 `/api/v1/health`
5. 加入最小 smoke test
6. 更新两个目录的 README，说明职责和边界

## Self-Review

- **Placeholder scan:** 无 `TODO`、`TBD` 或未决命名
- **Consistency check:** 与 `docs/architecture/api-boundary.md`、`contract-strategy.md` 的 API-first 和 shared-types 约束一致
- **Scope check:** 范围只覆盖 `L1-B` 的最小 shared-types + api 起步包，没有漂移到 DB、digest 或 Web
- **Ambiguity check:** 这轮明确只实现 `health`，未来资源只作为后续扩展方向，不在本轮实现
