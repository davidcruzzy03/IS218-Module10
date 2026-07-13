from datetime import datetime, timezone
import uuid

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate, UserRead


def test_valid_user_create_schema():
    """Valid registration data should pass validation."""

    user = UserCreate(
        username="davidcruz",
        email="david@example.com",
        password="SecurePass123",
    )

    assert user.username == "davidcruz"
    assert str(user.email) == "david@example.com"
    assert user.password == "SecurePass123"


def test_invalid_email_is_rejected():
    """An invalid email should fail Pydantic validation."""

    with pytest.raises(ValidationError):
        UserCreate(
            username="davidcruz",
            email="not-an-email",
            password="SecurePass123",
        )


def test_short_password_is_rejected():
    """A password under eight characters should fail."""

    with pytest.raises(ValidationError):
        UserCreate(
            username="davidcruz",
            email="david@example.com",
            password="short",
        )


def test_short_username_is_rejected():
    """A username under three characters should fail."""

    with pytest.raises(ValidationError):
        UserCreate(
            username="dc",
            email="david@example.com",
            password="SecurePass123",
        )


def test_username_with_invalid_characters_is_rejected():
    """Only the characters permitted by the schema should pass."""

    with pytest.raises(ValidationError):
        UserCreate(
            username="david cruz",
            email="david@example.com",
            password="SecurePass123",
        )


def test_user_read_does_not_include_password_fields():
    """The response schema must never expose password information."""

    user = UserRead(
        id=uuid.uuid4(),
        username="davidcruz",
        email="david@example.com",
        created_at=datetime.now(timezone.utc),
    )

    serialized_user = user.model_dump()

    assert "password" not in serialized_user
    assert "password_hash" not in serialized_user