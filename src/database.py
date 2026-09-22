import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text


load_dotenv()


def get_engine():
    """Create and return the PostgreSQL SQLAlchemy engine."""

    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        host = os.getenv("DB_HOST")
        port = os.getenv("DB_PORT")
        database = os.getenv("DB_NAME")
        user = os.getenv("DB_USER")
        password = os.getenv("DB_PASSWORD")

        database_url = (
            f"postgresql+psycopg2://{user}:{password}"
            f"@{host}:{port}/{database}"
        )

    return create_engine(database_url, pool_pre_ping=True)


def test_connection():
    """Test the database connection and display the connected database/user."""

    engine = get_engine()

    with engine.connect() as connection:
        result = connection.execute(
            text("SELECT current_database(), current_user;")
        )

        database, user = result.fetchone()

        print("PostgreSQL connection successful.")
        print(f"Database: {database}")
        print(f"User: {user}")


if __name__ == "__main__":
    test_connection()