
from fastapi.testclient import TestClient

from app.main import app
from app.rate_limit import request_history

client = TestClient(app)


def setup_function():
    # Clear previous request counts before each test.
    request_history.clear()


def test_requests_within_limit_are_processed():
    for _ in range(5):
        response = client.get("/users/me")
        assert response.status_code == 401

    # The sixth request should exceed the limit.
    response = client.get("/users/me")
    assert response.status_code == 429


def test_rate_limit_response_contains_retry_after():
    for _ in range(5):
        client.get("/users/me")

    response = client.get("/users/me")

    assert response.status_code == 429
    assert "Retry-After" in response.headers


def test_health_endpoint_is_excluded():
    for _ in range(6):
        response = client.get("/health")
        assert response.status_code == 200
