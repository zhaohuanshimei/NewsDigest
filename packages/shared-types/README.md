# packages/shared-types

V2 共享契约包。

## 定位

`packages/shared-types` 是 API 与客户端之间的共享契约层。这里只放对外公开 API 资源契约，不放数据库表类型、ORM 模型、或内部 service / repository 类型。

## 已实现契约

- `HealthResource`
- `ApiError`
- `DigestResource`
- `DigestEntryResource`
- `ArchiveDateListResource`
- `ClusterDetailResource`
- `ArticleDetailResource`

## 使用方式

### 手动维护类型（推荐）

从 `src/index.ts` 导入公开类型，不直接引用内部资源文件：

```typescript
import type { DigestResource, ApiError } from "@news-digest/shared-types";
```

手动维护的 TypeScript 类型位于 `src/resources/*.ts`，是前端消费的入口。

### 自动生成类型（参考对照）

运行导出管线后，TypeScript 类型会生成到 `src/generated/`：

```bash
# 1. 从 FastAPI app 导出 OpenAPI schema
python scripts/export-api-schema.py

# 2. 从 schema 生成 TypeScript 类型
python scripts/sync-shared-types.py
```

生成的类型用于与手动维护的类型做对照，帮助发现契约漂移。

## 契约变更流程

当某个功能需要新增或修改公开字段时，遵循以下顺序：

1. 先更新 API Pydantic schema（`services/api/app/schemas/`）
2. 运行 `python scripts/export-api-schema.py` 导出 schema
3. 运行 `python scripts/sync-shared-types.py` 生成 TypeScript 对照
4. 对比 `src/resources/`（手动）与 `src/generated/`（自动），同步差异
5. 更新 `src/resources/` 中对应的类型定义
6. 提交变更（schema + 类型一起提交）

## 兼容性规则

- **非破坏性变更**：新增可选字段、新增向后兼容的资源
- **破坏性变更**：删除字段、修改字段类型/含义、改变错误结构——必须在架构文档中记录

## 不放什么

- 数据库表定义
- ORM 模型
- 内部 service / repository 类型
- 只服务于某一个页面私有实现的临时类型

## CI 集成

CI 可以运行 schema 导出脚本并 diff 输出，确保 schema 变更不会被遗漏：

```bash
python scripts/export-api-schema.py
git diff --exit-code packages/shared-types/openapi.json
```
