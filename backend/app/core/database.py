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


# Lazy initialization - only create engine when first accessed
_engine = None
_sessionmaker = None


def _get_engine():
    """Get or create the engine lazily."""
    global _engine
    if _engine is None:
        _engine = get_engine()
    return _engine


def _get_sessionmaker():
    """Get or create the sessionmaker lazily."""
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = sessionmaker(bind=_get_engine(), autoflush=False, autocommit=False)
    return _sessionmaker


class LazyEngine:
    """Lazy proxy for engine that initializes on first access."""
    
    def __call__(self):
        return _get_engine()
    
    def __getattr__(self, name):
        return getattr(_get_engine(), name)


class LazySessionLocal:
    """Lazy proxy for SessionLocal that creates sessions on demand."""
    
    def __call__(self):
        """Create and return a new Session instance."""
        return _get_sessionmaker()()
    
    def __getattr__(self, name):
        """Proxy attributes to the sessionmaker for backward compatibility."""
        return getattr(_get_sessionmaker(), name)


# Lazy instances
engine = LazyEngine()
SessionLocal = LazySessionLocal()


def get_db() -> TypingGenerator[Session, None, None]:
    """Dependency injection for FastAPI endpoints."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Backward compatible accessor
def get_session_local():
    return _get_sessionmaker()