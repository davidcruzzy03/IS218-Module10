from app.models.user import User


def test_user_repr():
    user = User(
        username="davidcruz",
        email="david@example.com",
        password_hash="hashed-password",
    )

    representation = repr(user)

    assert "davidcruz" in representation
    assert "david@example.com" in representation