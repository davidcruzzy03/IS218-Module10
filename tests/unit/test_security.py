from app.security import hash_password, verify_password


def test_hash_password_does_not_store_plain_text():
    """A stored password must differ from the original password."""

    plain_password = "SecurePass123"
    password_hash = hash_password(plain_password)

    assert password_hash != plain_password
    assert isinstance(password_hash, str)
    assert len(password_hash) > 0


def test_verify_password_accepts_correct_password():
    """The correct password should match its hash."""

    plain_password = "SecurePass123"
    password_hash = hash_password(plain_password)

    assert verify_password(
        plain_password,
        password_hash,
    ) is True


def test_verify_password_rejects_wrong_password():
    """An incorrect password should not match the hash."""

    password_hash = hash_password("SecurePass123")

    assert verify_password(
        "WrongPassword123",
        password_hash,
    ) is False


def test_same_password_generates_different_hashes():
    """Bcrypt should create a new salted hash each time."""

    first_hash = hash_password("SecurePass123")
    second_hash = hash_password("SecurePass123")

    assert first_hash != second_hash