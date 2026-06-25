from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_archive_dates_route_returns_available_dates() -> None:
    response = client.get("/api/v1/archive/dates")

    assert response.status_code == 200
    assert response.json() == {
        "dates": ["2026-06-24", "2026-06-23"],
    }


def test_archive_dates_route_is_present_in_openapi() -> None:
    response = client.get("/openapi.json")
    schema = response.json()

    assert "/api/v1/archive/dates" in schema["paths"]
    get_operation = schema["paths"]["/api/v1/archive/dates"]["get"]
    assert get_operation["summary"] == "Get Archive Dates"
