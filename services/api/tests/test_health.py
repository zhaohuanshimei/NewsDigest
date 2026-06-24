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
