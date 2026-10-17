def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_health_alias(client):
    assert client.get("/api/health").status_code == 200


def test_categories_lists_known_values(client):
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    assert "Dairy" in resp.json()


def test_metrics_endpoint_exposes_prometheus_format(client):
    client.get("/api/items")
    resp = client.get("/metrics")
    assert resp.status_code == 200
    assert "http_requests_total" in resp.text
    assert "http_request_duration_seconds" in resp.text
