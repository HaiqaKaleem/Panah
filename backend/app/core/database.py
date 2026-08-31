import os
import warnings

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings

def _resolve_database_url() -> str:
    """Resolve database URL, falling back to SQLite if driver is missing."""
    url = settings.database_url
    if url.startswith("postgresql"):
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            warnings.warn(
                "psycopg2 not installed — falling back to SQLite for tests",
                stacklevel=2,
            )
            return "sqlite:///./panagah.db"
    return url

def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")

database_url = _resolve_database_url()
connect_args = {}
if _is_sqlite(database_url):
    connect_args["check_same_thread"] = False

engine = create_engine(
    database_url,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
