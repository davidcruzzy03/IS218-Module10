import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set this before importing the application database modules.
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fastapi_test_db",
)

from app.database import Base, get_db  # noqa: E402
from app.models.user import User  # noqa: E402, F401
from main import app  # noqa: E402


test_engine = create_engine(
    TEST_DATABASE_URL,
    pool_pre_ping=True,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """
    Create the database tables once for the test session.

    All tables are removed when the test session finishes.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def database():
    """
    Give each test a database session and roll back its work afterward.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(database):
    """Create a FastAPI client that uses the testing database session."""

    def override_get_db():
        try:
            yield database
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()