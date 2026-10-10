"""Database engine, session factory and FastAPI dependency."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings


def _normalize_database_url(url: str) -> str:
    # Providers like Render hand out `postgres://` URLs; SQLAlchemy expects
    # the `postgresql://` dialect name. Accept both so pasted URLs just work.
    if url.startswith("postgres://"):
        return "postgresql://" + url[len("postgres://"):]
    return url


database_url = _normalize_database_url(settings.database_url)
connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
engine = create_engine(database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """Yield a request-scoped DB session (FastAPI dependency)."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
