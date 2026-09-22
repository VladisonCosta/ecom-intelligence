from unittest.mock import patch

from src.database import get_engine


def test_get_engine_uses_database_url():
    database_url = "postgresql://test_user:test_password@test_host:5432/test_db"

    with patch.dict(
        "os.environ",
        {"DATABASE_URL": database_url},
        clear=True,
    ):
        engine = get_engine()

    assert str(engine.url) == (
        "postgresql://test_user:***@test_host:5432/test_db"
    )


def test_get_engine_uses_individual_database_variables():
    environment = {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "test_database",
        "DB_USER": "test_user",
        "DB_PASSWORD": "test_password",
    }

    with patch.dict("os.environ", environment, clear=True):
        engine = get_engine()

    assert engine.url.host == "localhost"
    assert engine.url.port == 5432
    assert engine.url.database == "test_database"
    assert engine.url.username == "test_user"
    assert engine.url.password == "test_password"