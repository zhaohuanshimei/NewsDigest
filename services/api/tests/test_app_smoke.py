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
