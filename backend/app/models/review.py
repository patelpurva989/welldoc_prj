"""Review models for FDA submission review workflow."""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    reviewer_name = Column(String(255))
    review_round = Column(Integer, default=1)
    status = Column(String(20), default="pending")
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    overall_notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    submission = relationship("Submission", back_populates="workflow_reviews")
    checklist_items = relationship("ReviewChecklistItem", back_populates="review", cascade="all, delete-orphan")


class ReviewChecklistItem(Base):
    __tablename__ = "review_checklist_items"

    id = Column(Integer, primary_key=True, index=True)
    review_id = Column(Integer, ForeignKey("reviews.id", ondelete="CASCADE"), nullable=False)
    section_number = Column(Integer, nullable=False)
    section_name = Column(String(255), nullable=False)
    is_complete = Column(Boolean, default=False)
    is_applicable = Column(Boolean, default=True)
    completeness_percent = Column(Integer, default=0)
    deficiency_level = Column(String(10))
    reviewer_notes = Column(Text)
    assignee = Column(String(255))
    checked_at = Column(DateTime)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    review = relationship("Review", back_populates="checklist_items")


class SubmissionStatusLog(Base):
    __tablename__ = "submission_status_logs"

    id = Column(Integer, primary_key=True, index=True)
    submission_id = Column(Integer, ForeignKey("submissions.id", ondelete="CASCADE"), nullable=False)
    previous_status = Column(String(50))
    new_status = Column(String(50))
    changed_by = Column(String(100))
    notes = Column(Text)
    changed_at = Column(DateTime, default=datetime.utcnow)
