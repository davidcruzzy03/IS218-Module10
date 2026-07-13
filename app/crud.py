from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate
from app.security import hash_password


def get_user_by_username(
    database: Session,
    username: str,
) -> User | None:
    """Return a user matching the supplied username."""

    statement = select(User).where(
        User.username == username
    )

    return database.scalar(statement)


def get_user_by_email(
    database: Session,
    email: str,
) -> User | None:
    """Return a user matching the supplied email."""

    statement = select(User).where(
        User.email == email
    )

    return database.scalar(statement)


def create_user(
    database: Session,
    user_data: UserCreate,
) -> User:
    """Hash a password and create a user record."""

    user = User(
        username=user_data.username,
        email=str(user_data.email),
        password_hash=hash_password(user_data.password),
    )

    database.add(user)
    database.commit()
    database.refresh(user)

    return user