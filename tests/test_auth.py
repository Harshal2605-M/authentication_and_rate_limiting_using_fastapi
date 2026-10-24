
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

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
