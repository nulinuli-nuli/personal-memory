"""Database connection and session management."""
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from src.shared.config import settings

# Convert relative path to absolute path for SQLite
db_url = settings.database_url
if db_url.startswith("sqlite:///"):
    # Extract the file path and make it absolute
    from pathlib import Path
    db_path = db_url.replace("sqlite:///", "")
    if not Path(db_path).is_absolute():
        # Make it relative to the project root (where this file is located)
        project_root = Path(__file__).parent.parent.parent
        absolute_db_path = project_root / db_path
        absolute_db_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{absolute_db_path}"

# Create engine
engine = create_engine(
    db_url,
    echo=settings.debug,
    connect_args={"check_same_thread": False} if db_url.startswith("sqlite") else {},
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Get database session context manager.

    Usage:
        with get_db() as db:
            db.query(...)
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables."""
    from src.shared.models import Base

    Base.metadata.create_all(bind=engine)


def drop_all_tables():
    """Drop all database tables (use with caution!)."""
    from src.shared.models import Base

    Base.metadata.drop_all(bind=engine)


def reset_db():
    """Drop all tables and recreate them (use with caution!)."""
    from src.shared.models import Base

    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
