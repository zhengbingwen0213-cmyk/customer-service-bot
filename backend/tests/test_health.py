from __future__ import annotations

from datetime import datetime

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)


def test_health_uses_contract_envelope() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["code"] == 200
    assert body["message"] == "success"
    assert body["data"]["status"] == "ok"
    assert body["data"]["service"] == "customer-service-bot-api"
    datetime.fromisoformat(body["data"]["time"])


def test_unknown_route_uses_error_envelope() -> None:
    response = client.get("/missing")

    assert response.status_code == 404
    assert response.json() == {
        "code": 404,
        "message": "Not Found",
        "data": None,
    }


def test_health_allows_configured_cors_origin() -> None:
    response = client.options(
        "/health",
        headers={
            "Origin": "http://localhost:5199",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://localhost:5199"
