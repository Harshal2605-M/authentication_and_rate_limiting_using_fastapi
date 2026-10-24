
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from datetime import datetime, timedelta, timezone
import jwt

from app.config import settings
from app.main import app
from app.database import Base, get_db
from app import models
from app.rate_limit import request_history


@pytest.fixture(autouse=True)
def isolated_test_database():
    # Create a separate in-memory database for this test.
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    request_history.clear()

    yield

    app.dependency_overrides.clear()
    request_history.clear()
    Base.metadata.drop_all(bind=test_engine)
    test_engine.dispose()


@pytest.fixture
def registered_user():
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={
                "email": "test-auth@example.com",
                "password": "TestPass123",
            },
        )

    assert response.status_code == 201

    return {
        "email": "test-auth@example.com",
        "password": "TestPass123",
    }


def test_register_user():
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={
                "email": "new-user@example.com",
                "password": "TestPass123",
            },
        )

    assert response.status_code == 201
    assert response.json()["email"] == "new-user@example.com"
    assert "hashed_password" not in response.json()


def test_duplicate_registration(registered_user):
    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={
                "email": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert response.status_code == 409


def test_login_with_wrong_password(registered_user):
    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            data={
                "username": registered_user["email"],
                "password": "WrongPassword123",
            },
        )

    assert response.status_code == 401


def test_protected_profile_without_token():
    with TestClient(app) as client:
        response = client.get("/users/me")

    assert response.status_code == 401


def test_login_success(registered_user):
    with TestClient(app) as client:
        response = client.post(
            "/auth/login",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 0


def test_valid_token_accesses_profile(registered_user):
    with TestClient(app) as client:
        login_response = client.post(
            "/auth/login",
            data={
                "username": registered_user["email"],
                "password": registered_user["password"],
            },
        )

        assert login_response.status_code == 200

        token = login_response.json()["access_token"]

        profile_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert profile_response.status_code == 200

    profile = profile_response.json()
    assert profile["email"] == registered_user["email"]



def test_invalid_token_is_rejected():
    with TestClient(app) as client:
        response = client.get(
            "/users/me",
            headers={
                "Authorization": "Bearer invalid.token.value"
            },
        )

    assert response.status_code == 401


def test_expired_token_is_rejected(registered_user):
    now = datetime.now(timezone.utc)

    expired_payload = {
        "sub": "1",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
    }

    expired_token = jwt.encode(
        expired_payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )

    with TestClient(app) as client:
        response = client.get(
            "/users/me",
            headers={
                "Authorization": f"Bearer {expired_token}"
            },
        )

    assert response.status_code == 401
