from sqlalchemy import select

from app.models.user import User
from app.security import verify_password


VALID_USER = {
    "username": "davidcruz",
    "email": "david@example.com",
    "password": "SecurePass123",
}


def test_create_user_successfully(client):
    """A valid user should be stored and returned."""

    response = client.post(
        "/users",
        json=VALID_USER,
    )

    assert response.status_code == 201

    data = response.json()

    assert data["username"] == "davidcruz"
    assert data["email"] == "david@example.com"
    assert "id" in data
    assert "created_at" in data


def test_response_does_not_expose_password(client):
    """The registration response must not expose password data."""

    response = client.post(
        "/users",
        json=VALID_USER,
    )

    assert response.status_code == 201

    data = response.json()

    assert "password" not in data
    assert "password_hash" not in data


def test_password_is_stored_as_hash(client, database):
    """PostgreSQL should contain a hash, not the submitted password."""

    response = client.post(
        "/users",
        json=VALID_USER,
    )

    assert response.status_code == 201

    statement = select(User).where(
        User.username == "davidcruz"
    )
    stored_user = database.scalar(statement)

    assert stored_user is not None
    assert stored_user.password_hash != "SecurePass123"
    assert verify_password(
        "SecurePass123",
        stored_user.password_hash,
    ) is True


def test_duplicate_username_is_rejected(client):
    """Two users cannot have the same username."""

    first_response = client.post(
        "/users",
        json={
            "username": "duplicateuser",
            "email": "first@example.com",
            "password": "SecurePass123",
        },
    )

    second_response = client.post(
        "/users",
        json={
            "username": "duplicateuser",
            "email": "second@example.com",
            "password": "AnotherPass123",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["error"]
        == "Username already exists"
    )


def test_duplicate_email_is_rejected(client):
    """Two users cannot have the same email address."""

    first_response = client.post(
        "/users",
        json={
            "username": "firstuser",
            "email": "duplicate@example.com",
            "password": "SecurePass123",
        },
    )

    second_response = client.post(
        "/users",
        json={
            "username": "seconduser",
            "email": "duplicate@example.com",
            "password": "AnotherPass123",
        },
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert (
        second_response.json()["error"]
        == "Email already exists"
    )


def test_invalid_email_is_rejected_by_api(client):
    """FastAPI should reject invalid Pydantic email data."""

    response = client.post(
        "/users",
        json={
            "username": "davidcruz",
            "email": "invalid-email",
            "password": "SecurePass123",
        },
    )

    # Your custom validation handler returns 400 instead of
    # FastAPI's default 422 response.
    assert response.status_code == 400


def test_short_password_is_rejected_by_api(client):
    """FastAPI should reject a password under eight characters."""

    response = client.post(
        "/users",
        json={
            "username": "davidcruz",
            "email": "david@example.com",
            "password": "short",
        },
    )

    assert response.status_code == 400


def test_created_user_has_timestamp(client):
    """The database should generate created_at automatically."""

    response = client.post(
        "/users",
        json=VALID_USER,
    )

    assert response.status_code == 201
    assert response.json()["created_at"] is not None


def test_health_endpoint(client):
    """The application health route should respond successfully."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}