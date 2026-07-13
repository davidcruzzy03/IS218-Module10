import os
import subprocess
import time
import urllib.error
import urllib.request

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# ---------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/fastapi_test_db",
)

# main.py reads DATABASE_URL, so make sure it uses the test
# database before importing the application.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL


# These imports must occur after setting DATABASE_URL.
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


# ---------------------------------------------------------
# PostgreSQL fixtures
# ---------------------------------------------------------

@pytest.fixture(scope="session", autouse=True)
def prepare_test_database():
    """
    Create all database tables before the test session.

    Remove the tables after all tests finish.
    """

    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    yield

    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def database():
    """
    Give each test a database session.

    All database changes are rolled back after the test.
    """

    connection = test_engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(
        bind=connection,
    )

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(database):
    """
    Create a FastAPI TestClient using the test database.
    """

    def override_get_db():
        yield database

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


# ---------------------------------------------------------
# E2E FastAPI server fixture
# ---------------------------------------------------------

@pytest.fixture(scope="session")
def fastapi_server():
    """
    Start a real FastAPI server for Playwright E2E tests.

    The fixture waits until the health endpoint responds before
    allowing the browser tests to continue.
    """

    server_url = "http://127.0.0.1:8001"

    environment = os.environ.copy()
    environment["DATABASE_URL"] = TEST_DATABASE_URL

    process = subprocess.Popen(
        [
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8001",
        ],
        env=environment,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    server_ready = False

    for _ in range(30):
        try:
            with urllib.request.urlopen(
                f"{server_url}/health",
                timeout=1,
            ) as response:
                if response.status == 200:
                    server_ready = True
                    break
        except (
            urllib.error.URLError,
            ConnectionError,
            TimeoutError,
        ):
            time.sleep(1)

    if not server_ready:
        process.terminate()

        try:
            output, _ = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()

        pytest.fail(
            "FastAPI server did not start for E2E tests.\n"
            f"Server output:\n{output}"
        )

    yield server_url

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()