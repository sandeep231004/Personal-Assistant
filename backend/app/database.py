"""
PostgreSQL database setup using SQLAlchemy (Neon serverless database).
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Debug: Print database URL to verify Neon connection
import logging
logger = logging.getLogger(__name__)
db_url_masked = settings.DATABASE_URL.split('@')[0] + '@***' if '@' in settings.DATABASE_URL else settings.DATABASE_URL[:30] + '...'
logger.info(f"🔌 Connecting to database: {db_url_masked}")

# Create PostgreSQL engine (Neon serverless database)
# Creates the connection engine to the database (like the bridge between Python and the DB).
engine = create_engine(
    settings.DATABASE_URL,
    # PostgreSQL connection pool settings
    pool_size=5,              # Number of connections to keep open
    max_overflow=10,          # Additional connections when pool is exhausted
    pool_pre_ping=True,       # Verify connections before use (important for serverless)
    echo=settings.DEBUG       # Log SQL queries in debug mode
)

# Create session factory
# Factory for creating database session objects (used for queries and transactions).

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
"""
sessionmaker() → returns a session factory class.
bind=engine → attaches this factory to the previously created database engine.
autocommit=False → transactions are not committed automatically; you must call commit() explicitly.
autoflush=False → prevents SQLAlchemy from automatically sending pending changes to the DB before a query (helps avoid side effects).
"""


# Base class for models
# Creates a base class that all ORM models (tables) will inherit from.
Base = declarative_base()


def get_db():  # Safely provides a database session to FastAPI routes
    """
    Dependency function to get database session.
    Use this in FastAPI endpoints with Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(): # Creates the actual database tables.
    """Initialize database - create all tables."""
    from app.models import Note, Conversation, Document  # Import models
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully!")
