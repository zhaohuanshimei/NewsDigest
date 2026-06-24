# V2 契约策略

## 目标

V2 需要一个稳定的共享契约层，确保：

- API 输出不会和 Web 消费理解脱节
- 前后端不会各自维护一套语义相近但不一致的类型
- 后续多客户端扩展时仍能围绕统一资源模型演进

这份文档定义 `packages/shared-types` 的定位、来源、同步规则和兼容策略。

## 契约来源

- API 资源模型是共享契约的单一事实来源。
- `packages/shared-types` 负责沉淀对外公开资源的类型定义与 schema。
- 数据库 schema、内部 ORM、任务状态对象都不是公共契约来源。

换句话说：

- 数据库描述“系统如何存”
- service/repository 描述“系统如何算”
- shared-types 描述“系统如何对外说”

## 契约边界

`packages/shared-types` 只应该包含：

- 对外公开资源模型
- API 错误对象
- 分页、列表、健康状态等通用响应结构
- 必要的枚举和共享命名

不应该包含：

- 数据库表定义
- ORM 模型
- 抓取、聚类、翻译的内部任务对象
- 只服务于某一个页面私有实现的临时类型

## 同步顺序

当某个功能需要新增或修改公开字段时，统一遵循以下顺序：

1. 先更新 API 资源定义和架构文档
2. 再更新 `packages/shared-types`
3. 然后更新 `services/api` 的实现
4. 最后更新 `apps/web` 或其他客户端消费层

不允许跳过前两步，直接让前端或后端私自扩字段。

## 契约命名规则

- 资源名称优先使用业务语义，如 `DigestResource`
- 避免直接使用表名作为公共资源名，如 `DailyDigestRow`
- 避免使用与视图强绑定的名字，如 `HomepageCardData`
- 错误模型统一归为 `ApiError`

## 兼容性规则

### 非破坏性变更

以下变更默认视为非破坏性：

- 新增可选字段
- 新增向后兼容的资源
- 新增错误码而不改变现有错误结构

### 破坏性变更

以下变更视为 breaking change：

- 删除已有字段
- 修改字段含义
- 改变字段类型
- 修改错误结构
- 更改路由语义导致旧客户端无法继续消费

breaking change 必须：

- 先在架构文档中明确记录
- 在计划或变更说明中标注影响面
- 与版本策略联动，而不是静默修改

## 禁止事项

- 前端自行声明一套与 API 不一致的资源字段名
- 后端直接把数据库字段原样暴露为公共契约
- 在未更新 `packages/shared-types` 的情况下修改公开响应结构
- 让某个客户端的临时需求反向污染所有公共资源

## 首发阶段最小资源集

L1 首发阶段建议至少在 shared-types 中稳定沉淀以下资源：

- `DigestResource`
- `DigestEntryResource`
- `ArchiveDateListResource`
- `ClusterDetailResource`
- `ArticleDetailResource`
- `HealthResource`
- `ApiError`

这些名称后续可以微调，但其语义和边界不应轻易改变。
