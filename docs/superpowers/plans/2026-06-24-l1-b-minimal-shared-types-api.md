# L1-B Minimal Shared Types + API Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the first runnable V2 code checkpoint by turning `packages/shared-types` into a real contract package and `services/api` into a minimal FastAPI service with `GET /api/v1/health`.

**Architecture:** This plan implements the smallest possible `shared-types + api` closed loop. `packages/shared-types` owns the public contract names and field shapes; `services/api` exposes the health route and OpenAPI docs using matching semantics, without introducing database access, digest logic, or code generation. The API skeleton is intentionally small but future-ready: the directory layout leaves room for `routers`, `schemas`, `services`, and `repositories` without forcing business logic into this phase.

**Tech Stack:** `TypeScript`, `FastAPI`, `Pydantic`, `uvicorn`, `pytest`, `httpx`

## Global Constraints

- Scope is limited to `packages/shared-types` and `services/api`.
- In scope: `HealthResource`, `ApiError`, `GET /api/v1/health`, `/openapi.json`, `/docs`, and minimal smoke tests.
- All runtime coupling must remain API-first; this phase does not add `apps/web` runtime code.
- Shared contracts must live in `packages/shared-types`; do not place ORM, database-row, or internal service types there.
- Out of scope: database, Alembic, crawling, clustering, digest generation, translation, and real `digest/archive/detail` endpoints.
- Do not introduce a heavy schema/codegen pipeline in this phase.
- Keep names aligned with the approved spec in `docs/superpowers/specs/2026-06-24-l1-b-minimal-shared-types-api-design.md`.

---

## File Structure

### `packages/shared-types`

- Create: `packages/shared-types/package.json`
- Create: `packages/shared-types/tsconfig.json`
- Create: `packages/shared-types/src/index.ts`
- Create: `packages/shared-types/src/resources/health.ts`
- Create: `packages/shared-types/src/resources/error.ts`
- Create: `packages/shared-types/test/contracts.test.ts`
- Modify: `packages/shared-types/README.md`

Responsibilities:

- `package.json`: package-local scripts for `typecheck`
- `tsconfig.json`: strict compile target for the package
- `src/resources/health.ts`: `HealthResource` contract
- `src/resources/error.ts`: `ApiError` contract
- `src/index.ts`: public export barrel
- `test/contracts.test.ts`: compile-only usage examples that fail if exports drift
- `README.md`: explain package scope and forbidden content

### `services/api`

- Create: `services/api/requirements.txt`
- Create: `services/api/requirements-dev.txt`
- Create: `services/api/app/__init__.py`
- Create: `services/api/app/main.py`
- Create: `services/api/app/core/__init__.py`
- Create: `services/api/app/core/config.py`
- Create: `services/api/app/core/metadata.py`
- Create: `services/api/app/routers/__init__.py`
- Create: `services/api/app/routers/health.py`
- Create: `services/api/app/schemas/__init__.py`
- Create: `services/api/app/schemas/health.py`
- Create: `services/api/app/schemas/error.py`
- Create: `services/api/app/services/__init__.py`
- Create: `services/api/app/repositories/__init__.py`
- Create: `services/api/tests/test_app_smoke.py`
- Create: `services/api/tests/test_health.py`
- Modify: `services/api/README.md`

Responsibilities:

- `requirements.txt`: runtime dependencies
- `requirements-dev.txt`: testing dependencies
- `app/main.py`: FastAPI app assembly
- `core/config.py`: API prefix and docs path constants
- `core/metadata.py`: app name and version constants
- `schemas/*.py`: Pydantic response model definitions
- `routers/health.py`: health route
- `tests/test_app_smoke.py`: docs and OpenAPI smoke checks
- `tests/test_health.py`: route response contract check
- `README.md`: explain local startup and scope boundary

---

### Task 1: Build `packages/shared-types` Contract Package

**Files:**
- Create: `packages/shared-types/package.json`
- Create: `packages/shared-types/tsconfig.json`
- Create: `packages/shared-types/src/index.ts`
- Create: `packages/shared-types/src/resources/health.ts`
- Create: `packages/shared-types/src/resources/error.ts`
- Create: `packages/shared-types/test/contracts.test.ts`
- Modify: `packages/shared-types/README.md`

**Interfaces:**
- Consumes: approved public names from `docs/superpowers/specs/2026-06-24-l1-b-minimal-shared-types-api-design.md`
- Produces:
  - `HealthResource = { status: "ok"; service: string; version: string }`
  - `ApiError = { code: string; message: string; request_id: string }`
  - barrel exports in `packages/shared-types/src/index.ts`

- [ ] **Step 1: Write the failing typecheck scaffold**

```json
// packages/shared-types/package.json
{
  "name": "@news-digest/shared-types",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "typecheck": "tsc -p tsconfig.json --noEmit"
  },
  "devDependencies": {
    "typescript": "^5.6.0"
  }
}
```

```json
// packages/shared-types/tsconfig.json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "strict": true,
    "noEmit": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*.ts", "test/**/*.ts"]
}
```

```ts
// packages/shared-types/test/contracts.test.ts
import type { ApiError, HealthResource } from "../src/index.js";

const health: HealthResource = {
  status: "ok",
  service: "news-digest-api",
  version: "0.1.0",
};

const error: ApiError = {
  code: "service_unavailable",
  message: "服务暂时不可用",
  request_id: "req_placeholder",
};

void health;
void error;
```

- [ ] **Step 2: Run typecheck to verify it fails**

Run: `cd /Users/celongzhao/20260424_NewsDigest/packages/shared-types && npm install && npm run typecheck`

Expected: FAIL with TypeScript errors indicating `../src/index.js` or the exported members do not exist yet.

- [ ] **Step 3: Write the minimal contract implementation**

```ts
// packages/shared-types/src/resources/health.ts
export interface HealthResource {
  status: "ok";
  service: string;
  version: string;
}
```

```ts
// packages/shared-types/src/resources/error.ts
export interface ApiError {
  code: string;
  message: string;
  request_id: string;
}
```

```ts
// packages/shared-types/src/index.ts
export type { HealthResource } from "./resources/health.js";
export type { ApiError } from "./resources/error.js";
```

```md
<!-- packages/shared-types/README.md -->
# packages/shared-types

V2 共享契约包。

## 当前内容

- `HealthResource`
- `ApiError`

## 边界

- 这里只放对外公开 API 资源契约
- 不放数据库表类型
- 不放 ORM 模型
- 不放内部 service / repository 类型
```

- [ ] **Step 4: Run typecheck to verify it passes**

Run: `cd /Users/celongzhao/20260424_NewsDigest/packages/shared-types && npm run typecheck`

Expected: PASS with no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add \
  packages/shared-types/package.json \
  packages/shared-types/tsconfig.json \
  packages/shared-types/src/index.ts \
  packages/shared-types/src/resources/health.ts \
  packages/shared-types/src/resources/error.ts \
  packages/shared-types/test/contracts.test.ts \
  packages/shared-types/README.md
git commit -m "feat(shared-types): add minimal health and error contracts"
```

### Task 2: Build the Minimal FastAPI App Shell

**Files:**
- Create: `services/api/requirements.txt`
- Create: `services/api/requirements-dev.txt`
- Create: `services/api/app/__init__.py`
- Create: `services/api/app/main.py`
- Create: `services/api/app/core/__init__.py`
- Create: `services/api/app/core/config.py`
- Create: `services/api/app/core/metadata.py`
- Create: `services/api/app/services/__init__.py`
- Create: `services/api/app/repositories/__init__.py`
- Create: `services/api/tests/test_app_smoke.py`
- Modify: `services/api/README.md`

**Interfaces:**
- Consumes:
  - API prefix `/api/v1`
  - app identity `news-digest-api`
  - version `0.1.0`
- Produces:
  - `app` object in `services/api/app/main.py`
  - OpenAPI available at `/openapi.json`
  - docs available at `/docs`

- [ ] **Step 1: Write the failing smoke test and dependency files**

```txt
# services/api/requirements.txt
fastapi==0.116.1
uvicorn==0.35.0
```

```txt
# services/api/requirements-dev.txt
-r requirements.txt
pytest==8.4.1
httpx==0.28.1
```

```python
# services/api/tests/test_app_smoke.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_docs_route_is_available() -> None:
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_route_is_available() -> None:
    response = client.get("/openapi.json")
    assert response.status_code == 200
    body = response.json()
    assert body["info"]["title"] == "News Digest API"
    assert body["info"]["version"] == "0.1.0"
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && python3 -m pip install -r requirements-dev.txt && python3 -m pytest tests/test_app_smoke.py -v`

Expected: FAIL with `ModuleNotFoundError` or import failure because `app.main` does not exist yet.

- [ ] **Step 3: Write the minimal app shell**

```python
# services/api/app/__init__.py
"""News Digest API application package."""
```

```python
# services/api/app/core/__init__.py
"""Core configuration and metadata for the API service."""
```

```python
# services/api/app/core/config.py
API_PREFIX = "/api/v1"
```

```python
# services/api/app/core/metadata.py
APP_NAME = "News Digest API"
APP_VERSION = "0.1.0"
SERVICE_NAME = "news-digest-api"
```

```python
# services/api/app/services/__init__.py
"""Service-layer package reserved for future business logic."""
```

```python
# services/api/app/repositories/__init__.py
"""Repository-layer package reserved for future data access code."""
```

```python
# services/api/app/main.py
from fastapi import FastAPI

from app.core.metadata import APP_NAME, APP_VERSION


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)
```

```md
<!-- services/api/README.md -->
# services/api

V2 API 服务最小骨架。

## 当前范围

- FastAPI 应用入口
- OpenAPI 文档
- 下一任务补入 `/api/v1/health`

## 本地运行

```bash
cd services/api
python3 -m pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```
```

- [ ] **Step 4: Run the smoke test to verify it passes**

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && python3 -m pytest tests/test_app_smoke.py -v`

Expected: PASS with 2 tests passing.

- [ ] **Step 5: Commit**

```bash
git add \
  services/api/requirements.txt \
  services/api/requirements-dev.txt \
  services/api/app/__init__.py \
  services/api/app/main.py \
  services/api/app/core/__init__.py \
  services/api/app/core/config.py \
  services/api/app/core/metadata.py \
  services/api/app/services/__init__.py \
  services/api/app/repositories/__init__.py \
  services/api/tests/test_app_smoke.py \
  services/api/README.md
git commit -m "feat(api): add minimal FastAPI app shell"
```

### Task 3: Add the Health Route and Response Schemas

**Files:**
- Create: `services/api/app/routers/__init__.py`
- Create: `services/api/app/routers/health.py`
- Create: `services/api/app/schemas/__init__.py`
- Create: `services/api/app/schemas/health.py`
- Create: `services/api/app/schemas/error.py`
- Create: `services/api/tests/test_health.py`
- Modify: `services/api/app/main.py`

**Interfaces:**
- Consumes:
  - `API_PREFIX = "/api/v1"` from `app.core.config`
  - `APP_VERSION` and `SERVICE_NAME` from `app.core.metadata`
  - shared contract semantics:
    - `HealthResource.status = "ok"`
    - `HealthResource.service = string`
    - `HealthResource.version = string`
    - `ApiError.code/message/request_id`
- Produces:
  - `router` in `app.routers.health`
  - `class HealthResource(BaseModel)`
  - `class ApiError(BaseModel)`
  - `GET /api/v1/health`

- [ ] **Step 1: Write the failing health route test**

```python
# services/api/tests/test_health.py
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health_route_returns_expected_payload() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "news-digest-api",
        "version": "0.1.0",
    }


def test_health_route_is_present_in_openapi() -> None:
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/api/v1/health" in schema["paths"]
    get_operation = schema["paths"]["/api/v1/health"]["get"]
    assert get_operation["summary"] == "Get Health"
```

- [ ] **Step 2: Run the health route test to verify it fails**

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && python3 -m pytest tests/test_health.py -v`

Expected: FAIL because `/api/v1/health` is not registered yet and returns `404`.

- [ ] **Step 3: Write the schemas and router**

```python
# services/api/app/routers/__init__.py
"""API router package."""
```

```python
# services/api/app/schemas/__init__.py
"""Pydantic schemas exposed by the API layer."""
```

```python
# services/api/app/schemas/health.py
from typing import Literal

from pydantic import BaseModel


class HealthResource(BaseModel):
    status: Literal["ok"]
    service: str
    version: str
```

```python
# services/api/app/schemas/error.py
from pydantic import BaseModel


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
```

```python
# services/api/app/routers/health.py
from fastapi import APIRouter

from app.core.metadata import APP_VERSION, SERVICE_NAME
from app.schemas.health import HealthResource


router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResource)
def get_health() -> HealthResource:
    return HealthResource(
        status="ok",
        service=SERVICE_NAME,
        version=APP_VERSION,
    )
```

```python
# services/api/app/main.py
from fastapi import FastAPI

from app.core.config import API_PREFIX
from app.core.metadata import APP_NAME, APP_VERSION
from app.routers.health import router as health_router


app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
)

app.include_router(health_router, prefix=API_PREFIX)
```

- [ ] **Step 4: Run the health tests to verify they pass**

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && python3 -m pytest tests/test_health.py tests/test_app_smoke.py -v`

Expected: PASS with 4 tests passing.

- [ ] **Step 5: Commit**

```bash
git add \
  services/api/app/routers/__init__.py \
  services/api/app/routers/health.py \
  services/api/app/schemas/__init__.py \
  services/api/app/schemas/health.py \
  services/api/app/schemas/error.py \
  services/api/app/main.py \
  services/api/tests/test_health.py
git commit -m "feat(api): add health route and schemas"
```

### Task 4: Align Docs and Final Verification

**Files:**
- Modify: `packages/shared-types/README.md`
- Modify: `services/api/README.md`

**Interfaces:**
- Consumes:
  - public contracts from `packages/shared-types/src/index.ts`
  - running route `GET /api/v1/health`
- Produces:
  - package README that defines shared-contract boundaries
  - service README that documents install, run, and test commands

- [ ] **Step 1: Tighten the READMEs to match the actual deliverable**

```md
<!-- packages/shared-types/README.md -->
# packages/shared-types

V2 共享契约包。

## 已实现契约

- `HealthResource`
- `ApiError`

## 使用方式

从 `src/index.ts` 导入公开类型，不直接引用内部资源文件。

## 不放什么

- 数据库表结构
- ORM 模型
- 内部 service / repository 类型
```

```md
<!-- services/api/README.md -->
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
```

- [ ] **Step 2: Run the final verification commands**

Run: `cd /Users/celongzhao/20260424_NewsDigest/packages/shared-types && npm run typecheck`

Expected: PASS

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && python3 -m pytest tests -v`

Expected: PASS

- [ ] **Step 3: Run the app manually and verify the endpoint**

Run: `cd /Users/celongzhao/20260424_NewsDigest/services/api && uvicorn app.main:app --reload`

Expected: server starts on `http://127.0.0.1:8000`

Run in another terminal: `curl http://127.0.0.1:8000/api/v1/health`

Expected:

```json
{"status":"ok","service":"news-digest-api","version":"0.1.0"}
```

- [ ] **Step 4: Commit**

```bash
git add packages/shared-types/README.md services/api/README.md
git commit -m "docs: align minimal shared-types and api readmes"
```

---

## Self-Review

- **Spec coverage:** The plan covers the approved scope: real `shared-types` package, minimal FastAPI shell, `GET /api/v1/health`, matching response semantics, smoke tests, and docs. It does not introduce database, digest, archive, or Web runtime code.
- **Placeholder scan:** No task contains `TODO`, `TBD`, “handle appropriately”, or omitted code. Every code-changing step includes exact file content or replacement content.
- **Type consistency:** `HealthResource` and `ApiError` are the only public contract names in this phase; the route path remains `GET /api/v1/health`; the response fields remain `status`, `service`, and `version` throughout the plan.
