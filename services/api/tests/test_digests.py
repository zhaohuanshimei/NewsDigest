from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_latest_digest_route_returns_expected_payload() -> None:
    response = client.get("/api/v1/digests/latest")

    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-06-24",
        "published_at": "2026-06-24T09:00:00Z",
        "entries": [
            {
                "cluster_id": "cluster-ai-chip-001",
                "rank": 1,
                "category": "technology",
                "headline": "AI 芯片与模型基础设施继续升温",
                "summary": "多家厂商围绕训练基础设施与推理部署发布新进展。",
                "source_count": 3,
            }
        ],
    }


def test_latest_digest_route_is_present_in_openapi() -> None:
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/api/v1/digests/latest" in schema["paths"]
    get_operation = schema["paths"]["/api/v1/digests/latest"]["get"]
    assert get_operation["summary"] == "Get Latest Digest"


def test_digest_by_date_route_returns_expected_payload() -> None:
    response = client.get("/api/v1/digests/2026-06-24")

    assert response.status_code == 200
    assert response.json() == {
        "date": "2026-06-24",
        "published_at": "2026-06-24T09:00:00Z",
        "entries": [
            {
                "cluster_id": "cluster-ai-chip-001",
                "rank": 1,
                "category": "technology",
                "headline": "AI 芯片与模型基础设施继续升温",
                "summary": "多家厂商围绕训练基础设施与推理部署发布新进展。",
                "source_count": 3,
            }
        ],
    }


def test_digest_by_date_route_returns_404_error_when_missing() -> None:
    response = client.get("/api/v1/digests/2026-06-01")

    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "digest_not_found",
            "message": "未找到指定日期的日报",
            "request_id": "req_static_digest_lookup",
        }
    }
