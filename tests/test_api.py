from fastapi.testclient import TestClient

from dsan6700_ml_service.api import app

client = TestClient(app)


def test_health_endpoint() -> None:
    """Verify that the health endpoint reports a healthy service."""
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
