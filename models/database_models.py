from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, UTC
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Database configuration
DATABASE_URL = settings.postgresql_db

# Create engine with connection pool management for Neon serverless
engine = create_engine(
    DATABASE_URL, 
    echo=False,
    pool_pre_ping=True,          # Ensures dead connections are removed before use
    pool_recycle=1800,           # Recycles connections older than 30 minutes
    pool_size=5,                 # Number of connections to maintain in pool
    max_overflow=10,             # Additional connections for traffic spikes
    connect_args={
        "connect_timeout": 10,   # Connection timeout in seconds
        "application_name": "mental_health_bot_app"  # Help identify connections in logs
    }
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create base class
Base = declarative_base()

# Enums for status fields (currently none in use)

class User(Base):
    """User table for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    username = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    allowed_email_entry = relationship("AllowedEmail", back_populates="user", uselist=False)
    audit_logs = relationship("AuditLog", back_populates="user")
    document_uploads = relationship("DocumentUpload")


class AllowedEmail(Base):
    """Table to store emails of organization members allowed to register."""
    __tablename__ = "allowed_emails"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    role = Column(String(50), nullable=False, default='staff') # e.g., 'staff', 'admin'
    is_registered = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Foreign key to link to the user who registered with this email
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    user = relationship("User", back_populates="allowed_email_entry")



class DocumentUpload(Base):
    """Track PDF uploads and their extracted content"""
    __tablename__ = "document_uploads"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # User who uploaded the document
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Document Group (for multi-document processing)
    document_group_id = Column(String(100), nullable=True)  # UUID string to group documents together
    
    # File Information
    original_filename = Column(String(255), nullable=False)
    s3_file_path = Column(String(500), nullable=False)  # S3 key/path
    file_size = Column(Integer, nullable=True)  # File size in bytes
    
    # Extracted Content
    extracted_text = Column(Text, nullable=True)  # OCR extracted text
    extraction_status = Column(String(20), default="pending")  # pending, completed, failed
    
    # Processing Information
    processing_started_at = Column(DateTime, nullable=True)
    processing_completed_at = Column(DateTime, nullable=True)
    processing_error = Column(Text, nullable=True)  # Error message if processing failed
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    user = relationship("User", overlaps="document_uploads")
    
    # Performance Indexes
    __table_args__ = (
        Index('idx_document_uploads_user_id', 'user_id'),
        Index('idx_document_uploads_created_at', 'created_at'),
        Index('idx_document_uploads_extraction_status', 'extraction_status'),
        Index('idx_document_uploads_group_id', 'document_group_id'),
    )

class AuditLog(Base):
    """Enhanced audit trail for HIPAA compliance and security monitoring"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Core Action Details
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    category = Column(String(100), nullable=False)  
    action_details = Column(String(500), nullable=True)

    # Database record that gets affected or added
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    
    # Location & Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    
    # Performance Indexes
    __table_args__ = (
        Index('idx_audit_logs_user_id', 'user_id'),
        Index('idx_audit_logs_category', 'category'),
        Index('idx_audit_logs_created_at', 'created_at'),
        Index('idx_audit_logs_table_name', 'table_name'),
        Index('idx_audit_logs_record_id', 'record_id'),
        Index('idx_audit_logs_ip_address', 'ip_address'),
    )

# Database dependency
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()