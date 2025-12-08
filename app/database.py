"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

# Connection pool settings optimized for Supabase Session Pooling
# Use session pooling (port 5432), NOT transaction pooling (port 6543)
# SQLAlchemy ORM requires session state which transaction pooling doesn't support

if "sqlite" in settings.DATABASE_URL:
    # SQLite configuration
    engine = create_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    # PostgreSQL/Supabase configuration with connection pooling
    engine = create_engine(
        settings.DATABASE_URL,
        pool_size=5,  # Number of connections to maintain
        max_overflow=10,  # Additional connections beyond pool_size
        pool_pre_ping=True,  # Verify connections before using (important for Supabase)
        pool_recycle=3600,  # Recycle connections after 1 hour (Supabase timeout is ~1 hour)
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


