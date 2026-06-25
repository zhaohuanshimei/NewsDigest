from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_article_detail_route_returns_expected_payload() -> None:
    response = client.get("/api/v1/articles/article-nvidia-001")

    assert response.status_code == 200
    assert response.json() == {
        "id": "article-nvidia-001",
        "cluster_id": "cluster-ai-chip-001",
        "title": "Nvidia partners outline new AI infrastructure roadmap",
        "summary": "厂商围绕 AI 训练与推理基础设施披露新的产品与合作计划。",
        "body": "This is a static article body used to validate the V2 article detail contract.",
        "source": "Example Tech Daily",
        "url": "https://example.com/articles/nvidia-ai-infrastructure-roadmap",
        "published_at": "2026-06-24T08:30:00Z",
        "language": "en",
    }


def test_article_detail_route_returns_404_error_when_missing() -> None:
    response = client.get("/api/v1/articles/article-missing-999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "article_not_found",
            "message": "未找到指定文章",
            "request_id": "req_static_article_lookup",
        }
    }


def test_article_detail_route_is_present_in_openapi() -> None:
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/api/v1/articles/{article_id}" in schema["paths"]
    get_operation = schema["paths"]["/api/v1/articles/{article_id}"]["get"]
    assert get_operation["summary"] == "Get Article Detail"
