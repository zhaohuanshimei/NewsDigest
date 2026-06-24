# Architecture Docs

这里沉淀 News Digest V2 的正式架构文档，作为实现前的设计基线。

## 文档索引

- `overview.md`：系统目标、模块边界、核心数据流与分层职责
- `domain-model.md`：核心实体、关系、状态与统一术语
- `api-boundary.md`：首发 API 资源模型、路由范围、错误模型与非目标范围
- `contract-strategy.md`：`packages/shared-types` 的来源、同步顺序与兼容规则
- `non-functional-targets.md`：性能、可访问性、SEO、稳定性与内容质量目标

## 使用约定

- 实现前先更新对应架构文档，再进入代码阶段。
- 如果 `claude.md`、主计划与架构文档描述冲突，以修正文档一致性为先，不要直接开始编码。
- `docs/context/` 提供的是 V1 提炼背景；这里记录的是 V2 的正式设计决策。
