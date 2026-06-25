# services/api

V2 API 服务最小骨架。

## 已实现内容

- FastAPI 应用入口
- OpenAPI 文档：`/openapi.json`
- Swagger UI：`/docs`
- 健康检查：`GET /api/v1/health`
- 最新日报：`GET /api/v1/digests/latest`（当前为静态样例响应）
- 指定日期日报：`GET /api/v1/digests/{date}`（当前仅内置 `2026-06-24` 样例）
- 归档日期列表：`GET /api/v1/archive/dates`（当前返回静态样例日期列表）
- 聚类详情：`GET /api/v1/clusters/{id}`（当前基于静态 digest 样例反推）
- 文章详情：`GET /api/v1/articles/{id}`（当前返回静态 article 样例）

## 安装

```bash
cd services/api
python3 -m pip install -r requirements-dev.txt
```

## 启动

```bash
uvicorn app.main:app --reload
```

## 测试

```bash
python3 -m pytest tests -v
```
