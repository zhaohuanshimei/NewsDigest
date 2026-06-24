# services/api

V2 API 服务最小骨架。

## 已实现内容

- FastAPI 应用入口
- OpenAPI 文档：`/openapi.json`
- Swagger UI：`/docs`
- 健康检查：`GET /api/v1/health`

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
