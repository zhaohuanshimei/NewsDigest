# packages/shared-types

V2 共享契约包。

## 已实现契约

- `HealthResource`
- `ApiError`

## 使用方式

从 `src/index.ts` 导入公开类型，不直接引用内部资源文件。

## 不放什么

- 这里只放对外公开 API 资源契约
- 不放数据库表类型
- 不放 ORM 模型
- 不放内部 service / repository 类型
