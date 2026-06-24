# V2 API 边界

## 文档目的

这份文档定义 L1 首发阶段的 API 资源边界，目标是：

- 让 `services/api` 有清晰的首发输出范围
- 让 `apps/web` 明确自己消费的是哪些资源
- 让 `packages/shared-types` 知道应该围绕哪些公开对象建立契约

它描述的是对外公共接口，不描述后端内部 repository、service、job 的实现方式。

## 版本约定

- 首发统一使用 `/api/v1` 前缀
- `v1` 代表首个公开可消费版本
- 所有新客户端默认以该版本为消费入口

## 首发资源范围

L1 首发阶段只开放以下只读资源：

- `GET /api/v1/digests/latest`
- `GET /api/v1/digests/{date}`
- `GET /api/v1/archive/dates`
- `GET /api/v1/clusters/{id}`
- `GET /api/v1/articles/{id}`
- `GET /api/v1/health`

这些资源足以支撑：

- Web 首页
- 归档页
- 详情页
- RSS 输出层的数据来源
- 部署与监控系统的健康探测

## 资源说明

### `GET /api/v1/digests/latest`

返回最近一个已发布日报。

**用途**

- 首页默认加载
- RSS 主 feed 首发数据来源

**返回重点**

- `date`
- `published_at`
- `entries`

### `GET /api/v1/digests/{date}`

返回指定日期日报。

**用途**

- 历史日期页
- 归档直链

**路径参数**

- `date`：格式为 `YYYY-MM-DD`

### `GET /api/v1/archive/dates`

返回可用日报日期列表。

**用途**

- 归档索引页
- 日期导航

### `GET /api/v1/clusters/{id}`

返回某个事件聚类详情。

**用途**

- 事件详情页
- 聚类级 SEO 页面

### `GET /api/v1/articles/{id}`

返回某篇代表文章或原始文章详情。

**用途**

- 阅读详情页
- 未来后台与调试页面的原始内容检查

### `GET /api/v1/health`

返回服务健康信息。

**用途**

- liveness / readiness 检查
- 生产监控和告警

## 响应原则

- 所有公开接口返回稳定资源对象，而不是数据库表行的直接镜像。
- Web 端消费的是资源语义，如 `Digest`、`DigestEntry`、`ClusterDetail`，不是后端内部 ORM 模型。
- 所有公开资源必须可被 `packages/shared-types` 描述。
- 首发阶段优先保证接口简单、稳定、易消费，不为了未来假设需求提前扩展过多字段。

## 错误模型

首发 API 使用统一错误对象：

```json
{
  "error": {
    "code": "digest_not_found",
    "message": "未找到指定日期的日报",
    "request_id": "req_123"
  }
}
```

### 约定

- `code`：机器可识别的稳定错误码
- `message`：面向人类可读的错误说明
- `request_id`：用于日志与排障追踪

### 常见错误场景

- 资源不存在：返回 `404`
- 参数非法：返回 `400`
- 服务暂不可用：返回 `503`

## 首发不纳入范围

以下能力明确不属于 L1 首发 API 范围：

- 后台写接口
- 认证与权限体系
- 复杂筛选
- 搜索建议
- 用户语言偏好写入
- 收藏、已读、订阅写接口
- 多客户端专用 SDK 接口

这些能力可以在 L2 或 L3 设计，但不应挤入首发 API 边界。

## 与前端的协作边界

- `apps/web` 只能通过 HTTP/API 消费这些资源
- 前端不得通过文件系统直接读取后端导出结果
- 如果 Web 页面需要新字段，应先修改 API 资源定义，再同步更新 shared types 与实现

## 与 shared-types 的关系

`packages/shared-types` 应至少围绕以下公开资源建模：

- `DigestResource`
- `DigestEntryResource`
- `ArchiveDateListResource`
- `ClusterDetailResource`
- `ArticleDetailResource`
- `HealthResource`

资源命名可以在实现时再微调，但必须保持语义稳定，并且不能和数据库表名直接混用。
