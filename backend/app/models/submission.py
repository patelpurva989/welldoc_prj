"""Database models for FDA submissions."""
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from ..core.database import Base


class SubmissionType(str, enum.Enum):
    """Submission type enumeration."""
    PREMARKET_510K = "510k"
    PMA = "pma"
    DE_NOVO = "de_novo"
    IDE = "ide"


class SubmissionStatus(str, enum.Enum):
    """Submission status enumeration."""
    DRAFT = "draft"
    GENERATING = "generating"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    SUBMITTED = "submitted"


class ComplianceStatus(str, enum.Enum):
    """Compliance status enumeration."""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    NEEDS_REVIEW = "needs_review"


class Submission(Base):
    """FDA submission model."""
    __tablename__ = "submissions"

    id = Column(Integer, primary_key=True, index=True)
    submission_type = Column(SQLEnum(SubmissionType), nullable=False)
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.DRAFT)
    device_name = Column(String(255), nullable=False)
    device_description = Column(Text)
    manufacturer = Column(String(255))
    indications_for_use = Column(Text)

    # Predicate device (for 510(k))
    predicate_device_name = Column(String(255))
    predicate_k_number = Column(String(50))

    # Clinical evidence
    clinical_data = Column(JSON)

    # Generated documents
    generated_submission = Column(Text)
    substantial_equivalence_analysis = Column(Text)

    # Compliance
    compliance_status = Column(SQLEnum(ComplianceStatus), default=ComplianceStatus.NEEDS_REVIEW)
    compliance_report = Column(JSON)

    # Progress tracking
    progress_percent = Column(Integer, default=0)
    review_deadline = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    submitted_at = Column(DateTime, nullable=True)

    # Relationships
    reviews = relationship("SubmissionReview", back_populates="submission", cascade="all, delete-orphan")
    adverse_events = relationship("AdverseEvent", back_populates="submission", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="submission", cascade="all, delete-orphan")
    workflow_reviews = relationship("Review", back_populates="submission", cascade="all, delete-orphan")


class SubmissionReview(Base):
    """Human-in-the-loop review model."""
    __tablename__ = "submission_reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=False)
    reviewer_name = Column(String(255))
    reviewer_email = Column(String(255))

    # Review details
    section_reviewed = Column(String(100))
    comments = Column(Text)
    suggested_changes = Column(Text)
    approved = Column(Integer, default=0)  # 0=pending, 1=approved, -1=rejected

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)

    # Relationships
    submission = relationship("Submission", back_populates="reviews")


class AdverseEvent(Base):
    """Adverse event monitoring model."""
    __tablename__ = "adverse_events"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id"), nullable=True)

    # Event details
    event_id = Column(String(100), unique=True)
    device_name = Column(String(255))
    event_type = Column(String(100))
    severity = Column(String(50))
    description = Column(Text)

    # Patient info (anonymized)
    patient_age = Column(Integer, nullable=True)
    patient_sex = Column(String(10), nullable=True)

    # Dates
    event_date = Column(DateTime, nullable=True)
    reported_date = Column(DateTime)

    # Analysis
    ai_analysis = Column(Text)
    risk_score = Column(Integer, default=0)  # 0-100

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    submission = relationship("Submission", back_populates="adverse_events")


class PredicateDevice(Base):
    """Predicate device database for substantial equivalence."""
    __tablename__ = "predicate_devices"

    id = Column(Integer, primary_key=True, index=True)
    k_number = Column(String(50), unique=True, index=True)
    device_name = Column(String(255), nullable=False)
    manufacturer = Column(String(255))
    device_class = Column(String(10))
    product_code = Column(String(10))

    # Technical characteristics
    indications_for_use = Column(Text)
    technological_characteristics = Column(JSON)
    performance_data = Column(JSON)

    # Decision
    decision_date = Column(DateTime)
    decision = Column(String(50))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
