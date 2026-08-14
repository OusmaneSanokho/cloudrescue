from app import app


def test_health_returns_ok_status():
    client = app.test_client()
    response = client.get("/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "hostname" in data
    assert "version" in data