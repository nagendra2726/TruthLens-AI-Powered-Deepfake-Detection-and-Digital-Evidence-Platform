"""
DeepSafe Database Module
SQLAlchemy ORM models and database session management for storing analysis history.
Supports PostgreSQL (with connection pooling) and SQLite.
"""

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Float,
    Boolean,
    DateTime,
    Text,
)
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
import logging

logger = logging.getLogger("deepsafe.database")

# Database configuration: Switchable via DATABASE_URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./deepsafe_history.db")
# Fix Heroku/Render postgres:// URI schema if present
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

if "sqlite" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
else:
    # PostgreSQL enterprise connection pooling
    engine = create_engine(
        DATABASE_URL,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True,
        pool_recycle=3600,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisHistory(Base):
    """Store forensic analysis results for auditing, integrity verification, and legal reporting."""

    __tablename__ = "analysis_history"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, index=True, nullable=True)  # User who ran the analysis
    media_type = Column(String, nullable=False)  # image, video, audio
    media_name = Column(String, nullable=True)

    # Ingestion-Time Cryptographic Integrity
    original_media_sha256 = Column(String, index=True, nullable=True)
    media_byte_size = Column(Integer, nullable=True)

    # Analysis Results
    verdict = Column(String, nullable=False)  # "real" or "fake"
    confidence = Column(Float, nullable=False)
    ensemble_method = Column(String, nullable=False)  # "stacking", "voting", "average"
    ensemble_score = Column(Float, nullable=False)

    # Trustworthiness & Resilience Flags
    needs_human_review = Column(Boolean, default=False, nullable=True)
    disagreement_score = Column(Float, default=0.0, nullable=True)
    degraded_mode = Column(Boolean, default=False, nullable=True)

    # Metadata & Auditing
    inference_time = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Full JSON response payload
    full_response = Column(Text, nullable=True)

    def __repr__(self):
        return f"<AnalysisHistory(id={self.id}, request_id={self.request_id}, sha256={self.original_media_sha256}, verdict={self.verdict})>"


class ApiKey(Base):
    """Store API keys, usage, and tiers for developer and enterprise access."""

    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    key = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, default="Default Key")
    tier = Column(String, default="free")
    requests_used = Column(Integer, default=0)
    requests_limit = Column(Integer, default=100)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)

    def __repr__(self):
        return f"<ApiKey(id={self.id}, key={self.key[:8]}..., tier={self.tier}, used={self.requests_used}/{self.requests_limit})>"


def init_db():
    """Initialize database tables with SQLite backward-compatible column migration."""
    # Deduplicate any table indexes that may have been registered multiple times
    for table in Base.metadata.tables.values():
        seen_names = set()
        for idx in list(table.indexes):
            if idx.name in seen_names:
                table.indexes.remove(idx)
            else:
                seen_names.add(idx.name)

    Base.metadata.create_all(bind=engine)
    
    # SQLite graceful column additions if upgrading existing DB
    if "sqlite" in DATABASE_URL:
        import sqlite3
        db_path = DATABASE_URL.replace("sqlite:///", "")
        if os.path.exists(db_path):
            try:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(analysis_history)")
                existing_cols = {row[1] for row in cursor.fetchall()}
                new_cols = [
                    ("original_media_sha256", "TEXT"),
                    ("media_byte_size", "INTEGER"),
                    ("needs_human_review", "BOOLEAN DEFAULT 0"),
                    ("disagreement_score", "REAL DEFAULT 0.0"),
                    ("degraded_mode", "BOOLEAN DEFAULT 0"),
                ]
                for col_name, col_type in new_cols:
                    if col_name not in existing_cols:
                        cursor.execute(f"ALTER TABLE analysis_history ADD COLUMN {col_name} {col_type}")
                conn.commit()
                conn.close()
            except Exception as e:
                logger.debug(f"SQLite migration check notice: {e}")


def get_db():
    """Dependency for FastAPI routes to get DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
