import os
from typing import Generator as TypingGenerator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def get_engine():
    """Lazy engine creation to avoid startup issues on serverless platforms."""
    settings = get_settings()
    if not settings.database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured. "
            "Please set DATABASE_URL, POSTGRES_URL, or POSTGRES_URL_NON_POOLING environment variable."
        )
    
    # Check for default/invalid URL in production
    if "localhost" in settings.database_url and settings.app_env.lower() == "production":
        raise RuntimeError(
            f"Invalid DATABASE_URL in production: {settings.database_url}. "
            "Please configure a valid database connection string."
        )
    
    engine_kwargs: dict[str, object] = {"pool_pre_ping": True}
    if settings.database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
    elif os.getenv("VERCEL"):
        # Serverless workers are short-lived and may reuse stale pooled connections.
        engine_kwargs["poolclass"] = NullPool
    
    return create_engine(settings.database_url, **engine_kwargs)


class LazyEngine:
    """Lazy proxy for engine that initializes on first access."""
    _engine = None
    
    def __call__(self):
        if self._engine is None:
            self._engine = get_engine()
        return self._engine
    
    def __getattr__(self, name):
        return getattr(self(), name)


class LazySessionLocal:
    """Lazy proxy for SessionLocal that initializes on first access."""
    _session_local = None
    
    def __call__(self):
        if self._session_local is None:
            self._session_local = sessionmaker(bind=LazyEngine()(), autoflush=False, autocommit=False)
        return self._session_local
    
    def __getattr__(self, name):
        return getattr(self(), name)


# Lazy instances
engine = LazyEngine()
SessionLocal = LazySessionLocal()


def get_db() -> TypingGenerator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Backward compatible accessor
def get_session_local():
    return SessionLocal()
