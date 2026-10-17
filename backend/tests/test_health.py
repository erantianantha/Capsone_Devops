def test_health_returns_ok(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_api_health_alias(client):
    assert client.get("/api/health").status_code == 200


def test_ready_checks_database(client):
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready", "database": "up"}


def test_ready_returns_503_when_database_down(client):
    from sqlalchemy.exc import OperationalError

    from app.database import get_db
    from app.main import app

    class BrokenSession:
        def execute(self, *_):
            raise OperationalError("SELECT 1", {}, Exception("db down"))

    app.dependency_overrides[get_db] = lambda: BrokenSession()
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["database"] == "down"


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
