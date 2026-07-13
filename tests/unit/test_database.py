from app.database import get_db


def test_get_db_yields_and_closes_session():
    database_generator = get_db()
    database = next(database_generator)

    assert database is not None

    database_generator.close()