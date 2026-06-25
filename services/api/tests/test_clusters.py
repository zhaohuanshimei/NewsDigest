from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_cluster_detail_route_returns_expected_payload() -> None:
    response = client.get("/api/v1/clusters/cluster-ai-chip-001")

    assert response.status_code == 200
    assert response.json() == {
        "id": "cluster-ai-chip-001",
        "category": "technology",
        "headline": "AI 芯片与模型基础设施继续升温",
        "summary": "多家厂商围绕训练基础设施与推理部署发布新进展。",
        "source_count": 3,
        "digest_dates": ["2026-06-24"],
    }


def test_cluster_detail_route_returns_404_error_when_missing() -> None:
    response = client.get("/api/v1/clusters/cluster-missing-999")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "cluster_not_found",
            "message": "未找到指定聚类",
            "request_id": "req_static_cluster_lookup",
        }
    }


def test_cluster_detail_route_is_present_in_openapi() -> None:
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/api/v1/clusters/{cluster_id}" in schema["paths"]
    get_operation = schema["paths"]["/api/v1/clusters/{cluster_id}"]["get"]
    assert get_operation["summary"] == "Get Cluster Detail"
