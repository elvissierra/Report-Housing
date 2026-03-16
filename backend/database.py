import os
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


DEFAULT_DATABASE_URL = "sqlite:///./ra_runs.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
if ENVIRONMENT == "production" and DATABASE_URL.startswith("sqlite"):
    raise RuntimeError(
        "SQLite cannot be used in production. "
        "Set DATABASE_URL to a PostgreSQL connection string, "
        "e.g. postgresql://user:pass@host/dbname"
    )


def _is_sqlite(url: str) -> bool:
    return url.startswith("sqlite")


def _build_engine(database_url: str) -> Engine:
    """
    Build the SQLAlchemy engine with backend-specific options.

    - Postgres gets connection health checks that are better suited for a
      longer-running API service.
    """
    engine_kwargs = {
        "future": True,
        "echo": False,
    }

    if _is_sqlite(database_url):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    else:
        engine_kwargs["pool_pre_ping"] = True
        engine_kwargs["pool_recycle"] = 1800

    return create_engine(database_url, **engine_kwargs)


engine = _build_engine(DATABASE_URL)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    future=True,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that provides a database session per request
    and guarantees cleanup.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()