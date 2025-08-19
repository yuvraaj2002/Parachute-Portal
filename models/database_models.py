from sqlalchemy import create_engine, Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, Index, JSON, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime, UTC
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings
import enum

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

# Enums for status fields
class TicketStatus(str, enum.Enum):
    READY_FOR_REVIEW = "ready_for_review"
    NEEDS_PA = "needs_pa"
    PA_SUBMITTED = "pa_submitted"
    PA_APPROVED = "pa_approved"
    PA_DENIED = "pa_denied"
    READY_FOR_BILLING = "ready_for_billing"
    BILLED = "billed"
    PAID = "paid"
    DENIED = "denied"
    READY_FOR_FULFILLMENT = "ready_for_fulfillment"
    FULFILLED = "fulfilled"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class PAStatus(str, enum.Enum):
    NOT_REQUIRED = "not_required"
    REQUIRED = "required"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    DENIED = "denied"
    PENDING = "pending"

class BillingStatus(str, enum.Enum):
    NOT_READY = "not_ready"
    READY = "ready"
    SUBMITTED = "submitted"
    PAID = "paid"
    DENIED = "denied"
    RESUBMITTED = "resubmitted"

class FulfillmentStatus(str, enum.Enum):
    NOT_READY = "not_ready"
    READY = "ready"
    PACKED = "packed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"

class FormStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    COMPLETED = "completed"
    OVERDUE = "overdue"

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
    assigned_tickets = relationship("PatientTicket", back_populates="assigned_staff")
    notes = relationship("TicketNote", back_populates="staff_member")
    tasks = relationship("StaffTask", back_populates="assigned_staff")

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

class PatientTicket(Base):
    """Main patient ticket table for workflow management"""
    __tablename__ = "patient_tickets"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    parachute_case_id = Column(String(100), unique=True, nullable=False, index=True)
    ticket_number = Column(String(50), unique=True, nullable=False, index=True)
    
    # Patient Information
    patient_name = Column(String(100), nullable=False)
    patient_dob = Column(DateTime, nullable=False)
    patient_phone = Column(String(20), nullable=False)
    patient_email = Column(String(255), nullable=False)
    
    # Product & Medical Information
    product_requested = Column(String(100), nullable=False)
    hcpcs_code = Column(String(20), nullable=False)
    diagnosis_icd10 = Column(String(20), nullable=False)
    prescription_file_url = Column(String(500), nullable=True)
    
    # Insurance Information
    insurance_provider = Column(String(100), nullable=True)
    insurance_group_number = Column(String(50), nullable=True)
    insurance_member_id = Column(String(50), nullable=True)
    insurance_verified = Column(Boolean, default=False)
    
    # Provider Information
    ordering_provider_name = Column(String(100), nullable=False)
    provider_npi = Column(String(20), nullable=True)
    referral_source = Column(String(100), nullable=True)
    
    # Status & Flags
    qualified_flag = Column(Boolean, default=False)
    ticket_status = Column(Enum(TicketStatus), default=TicketStatus.READY_FOR_REVIEW)
    pa_required = Column(Boolean, default=False)
    pa_status = Column(Enum(PAStatus), default=PAStatus.NOT_REQUIRED)
    billing_status = Column(Enum(BillingStatus), default=BillingStatus.NOT_READY)
    fulfillment_status = Column(Enum(FulfillmentStatus), default=FulfillmentStatus.NOT_READY)
    
    # Staff Assignment
    assigned_staff_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    assigned_staff = relationship("User", back_populates="assigned_tickets")
    pa_requests = relationship("PARequest", back_populates="patient_ticket")
    billing_entries = relationship("BillingEntry", back_populates="patient_ticket")
    fulfillment_records = relationship("FulfillmentRecord", back_populates="patient_ticket")
    forms = relationship("PatientForm", back_populates="patient_ticket")
    notes = relationship("TicketNote", back_populates="patient_ticket")
    tasks = relationship("StaffTask", back_populates="patient_ticket")
    refills = relationship("RefillSchedule", back_populates="patient_ticket")
    communications = relationship("PatientCommunication", back_populates="patient_ticket")

class PARequest(Base):
    """Prior Authorization request tracking"""
    __tablename__ = "pa_requests"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # PA Details
    pa_number = Column(String(100), nullable=True)
    request_date = Column(DateTime, nullable=False)
    submission_date = Column(DateTime, nullable=True)
    response_date = Column(DateTime, nullable=True)
    status = Column(Enum(PAStatus), nullable=False)
    
    # Files
    request_file_url = Column(String(500), nullable=True)
    response_file_url = Column(String(500), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="pa_requests")

class InsuranceVerification(Base):
    """Insurance verification records"""
    __tablename__ = "insurance_verifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Verification Details
    verification_date = Column(DateTime, nullable=False)
    verified_by = Column(Integer, ForeignKey('users.id'), nullable=False)
    verification_method = Column(String(50), nullable=False)  # phone, online, fax
    
    # Coverage Details
    deductible_met = Column(Boolean, nullable=True)
    deductible_amount = Column(Float, nullable=True)
    deductible_remaining = Column(Float, nullable=True)
    coverage_percentage = Column(Float, nullable=True)  # 80.0 for 80%
    allowed_amount = Column(Float, nullable=True)
    
    # Patient Responsibility
    estimated_patient_cost = Column(Float, nullable=True)
    insurance_portion = Column(Float, nullable=True)
    
    # Status
    verification_status = Column(String(20), default="verified")  # verified, denied, pending
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket")
    verified_by_user = relationship("User")

class BillingEntry(Base):
    """Billing submission and tracking"""
    __tablename__ = "billing_entries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Billing Details
    payer_name = Column(String(100), nullable=False)
    submission_date = Column(DateTime, nullable=False)
    amount_billed = Column(Float, nullable=False)
    claim_id = Column(String(100), nullable=True)
    status = Column(Enum(BillingStatus), nullable=False)
    
    # Resubmission Info
    resubmission_count = Column(Integer, default=0)
    original_claim_id = Column(String(100), nullable=True)
    
    # Attachments
    cmn_file_url = Column(String(500), nullable=True)
    pa_file_url = Column(String(500), nullable=True)
    rx_file_url = Column(String(500), nullable=True)
    eligibility_screenshot_url = Column(String(500), nullable=True)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="billing_entries")

class FulfillmentRecord(Base):
    """Fulfillment and delivery tracking"""
    __tablename__ = "fulfillment_records"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Fulfillment Details
    order_packed_date = Column(DateTime, nullable=True)
    shipped_date = Column(DateTime, nullable=True)
    delivered_date = Column(DateTime, nullable=True)
    
    # Shipping Information
    shipping_method = Column(String(50), nullable=True)
    tracking_number = Column(String(100), nullable=True)
    carrier = Column(String(50), nullable=True)
    
    # Status
    status = Column(Enum(FulfillmentStatus), nullable=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="fulfillment_records")

class PatientForm(Base):
    """Patient form automation and tracking"""
    __tablename__ = "patient_forms"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Form Details
    form_type = Column(String(50), nullable=False)  # medicare_packet, pod, aob, supplier_agreement
    form_name = Column(String(100), nullable=False)
    form_url = Column(String(500), nullable=False)
    
    # Status
    status = Column(Enum(FormStatus), default=FormStatus.PENDING)
    sent_date = Column(DateTime, nullable=True)
    completed_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    
    # Patient Response
    patient_response_url = Column(String(500), nullable=True)
    signature_received = Column(Boolean, default=False)
    
    # Auto-fill Data
    auto_fill_data = Column(JSON, nullable=True)  # Patient + RX data for form population
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="forms")

class RefillSchedule(Base):
    """Refill and resupply scheduling"""
    __tablename__ = "refill_schedules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Refill Details
    refill_cycle_days = Column(Integer, nullable=False)  # 30, 60, 90 days
    next_refill_date = Column(DateTime, nullable=False)
    last_refill_date = Column(DateTime, nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    refill_sent = Column(Boolean, default=False)
    refill_sent_date = Column(DateTime, nullable=True)
    
    # Notifications
    patient_notified = Column(Boolean, default=False)
    staff_reminder_sent = Column(Boolean, default=False)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="refills")

class StaffTask(Base):
    """Staff task management"""
    __tablename__ = "staff_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    assigned_staff_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Task Details
    task_title = Column(String(200), nullable=False)
    task_description = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)  # pa_request, billing, fulfillment, follow_up
    
    # Status
    is_completed = Column(Boolean, default=False)
    completed_date = Column(DateTime, nullable=True)
    due_date = Column(DateTime, nullable=True)
    priority = Column(String(20), default="medium")  # low, medium, high, urgent
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="tasks")
    assigned_staff = relationship("User", back_populates="tasks")

class TicketNote(Base):
    """Notes and comments on patient tickets"""
    __tablename__ = "ticket_notes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    staff_member_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    
    # Note Details
    note_content = Column(Text, nullable=False)
    note_type = Column(String(50), default="general")  # general, pa_update, billing_update, etc.
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="notes")
    staff_member = relationship("User", back_populates="notes")

class PatientCommunication(Base):
    """Patient communication and messaging tracking"""
    __tablename__ = "patient_communications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_ticket_id = Column(Integer, ForeignKey('patient_tickets.id'), nullable=False)
    
    # Communication Details
    communication_type = Column(String(50), nullable=False)  # sms, email, phone
    message_content = Column(Text, nullable=False)
    message_subject = Column(String(200), nullable=True)
    
    # Status
    sent = Column(Boolean, default=False)
    sent_date = Column(DateTime, nullable=True)
    delivered = Column(Boolean, default=False)
    delivered_date = Column(DateTime, nullable=True)
    
    # Trigger Information
    trigger_type = Column(String(50), nullable=True)  # post_delivery, refill_reminder, incomplete_docs, win_back
    automated = Column(Boolean, default=False)
    
    # Recipient
    recipient_phone = Column(String(20), nullable=True)
    recipient_email = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    patient_ticket = relationship("PatientTicket", back_populates="communications")

class AuditLog(Base):
    """Audit trail for HIPAA compliance"""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Action Details
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    action = Column(String(100), nullable=False)
    table_name = Column(String(100), nullable=False)
    record_id = Column(Integer, nullable=True)
    
    # Changes
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=lambda: datetime.now(UTC))
    
    # Relationships
    user = relationship("User")

# Database dependency
def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()