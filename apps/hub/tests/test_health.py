from __future__ import annotations

from fastapi.testclient import TestClient
from pitwall_hub.app import app

client = TestClient(app)


def test_health_reports_schema_state() -> None:
    response = client.get("/health")
    assert response.status_code == 200

    body = response.json()
    assert body["status"] == "ok"
    assert body["protocol_version"] >= 1
    # The hub is useless if it starts without a channel dictionary loaded.
    assert body["channel_count"] > 0
