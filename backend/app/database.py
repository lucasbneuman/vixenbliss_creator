import os
import uuid as uuid_pkg
from sqlalchemy import create_engine, TypeDecorator, String, CHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.dialects.postgresql import UUID as PostgreSQL_UUID
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


# GUID type that works with both SQLite and PostgreSQL
class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PostgreSQL_UUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return str(value)
        else:
            if isinstance(value, uuid_pkg.UUID):
                return str(value)
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if isinstance(value, uuid_pkg.UUID):
                return value
            else:
                return uuid_pkg.UUID(value)

# SQLite specific configuration
if DATABASE_URL and DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # Needed for SQLite
        echo=True if os.getenv("ENVIRONMENT") == "development" else False
    )
else:
    # PostgreSQL configuration
    engine = create_engine(
        DATABASE_URL,
        poolclass=NullPool,  # Disable connection pooling for serverless
        echo=True if os.getenv("ENVIRONMENT") == "development" else False
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class for models
Base = declarative_base()

# Dependency for FastAPI routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
