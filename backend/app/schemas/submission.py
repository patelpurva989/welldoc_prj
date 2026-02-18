"""Pydantic schemas for FDA submissions."""
from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional
from ..models.submission import SubmissionType, SubmissionStatus, ComplianceStatus


class SubmissionBase(BaseModel):
    """Base submission schema."""
    submission_type: SubmissionType
    device_name: str
    device_description: Optional[str] = None
    manufacturer: Optional[str] = None
    indications_for_use: Optional[str] = None
    predicate_device_name: Optional[str] = None
    predicate_k_number: Optional[str] = None


class SubmissionCreate(SubmissionBase):
    """Schema for creating a submission."""
    clinical_data: Optional[dict] = None


class SubmissionUpdate(BaseModel):
    """Schema for updating a submission."""
    device_name: Optional[str] = None
    device_description: Optional[str] = None
    manufacturer: Optional[str] = None
    indications_for_use: Optional[str] = None
    predicate_device_name: Optional[str] = None
    predicate_k_number: Optional[str] = None
    clinical_data: Optional[dict] = None
    status: Optional[SubmissionStatus] = None


class SubmissionResponse(SubmissionBase):
    """Schema for submission response."""
    id: int
    status: SubmissionStatus
    compliance_status: ComplianceStatus
    generated_submission: Optional[str] = None
    substantial_equivalence_analysis: Optional[str] = None
    compliance_report: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    submitted_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GenerateSubmissionRequest(BaseModel):
    """Request to generate submission documents."""
    submission_id: int
    include_predicate_analysis: bool = True
    include_clinical_summary: bool = True


class GenerateSubmissionResponse(BaseModel):
    """Response from document generation."""
    submission_id: int
    generated_submission: str
    substantial_equivalence_analysis: Optional[str] = None
    compliance_check: dict
    status: str = "success"


class ReviewCreate(BaseModel):
    """Schema for creating a review."""
    submission_id: int
    reviewer_name: str
    reviewer_email: EmailStr
    section_reviewed: str
    comments: str
    suggested_changes: Optional[str] = None
    approved: int = Field(default=0, ge=-1, le=1)


class ReviewResponse(BaseModel):
    """Schema for review response."""
    id: int
    submission_id: int
    reviewer_name: str
    reviewer_email: str
    section_reviewed: str
    comments: str
    suggested_changes: Optional[str] = None
    approved: int
    created_at: datetime
    reviewed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdverseEventCreate(BaseModel):
    """Schema for creating adverse event."""
    submission_id: Optional[int] = None
    device_name: str
    event_type: str
    severity: str
    description: str
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None
    event_date: Optional[datetime] = None


class AdverseEventResponse(BaseModel):
    """Schema for adverse event response."""
    id: int
    submission_id: Optional[int] = None
    event_id: str
    device_name: str
    event_type: str
    severity: str
    description: str
    ai_analysis: Optional[str] = None
    risk_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class PredicateDeviceSearch(BaseModel):
    """Schema for searching predicate devices."""
    device_name: Optional[str] = None
    product_code: Optional[str] = None
    device_class: Optional[str] = None
    indications_for_use: Optional[str] = None


class PredicateDeviceResponse(BaseModel):
    """Schema for predicate device response."""
    id: int
    k_number: str
    device_name: str
    manufacturer: Optional[str] = None
    device_class: Optional[str] = None
    product_code: Optional[str] = None
    indications_for_use: Optional[str] = None
    decision: Optional[str] = None
    decision_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class ComplianceCheckRequest(BaseModel):
    """Request for 21 CFR Part 11 compliance check."""
    submission_id: int
    check_electronic_signatures: bool = True
    check_audit_trail: bool = True
    check_record_retention: bool = True


class ComplianceCheckResponse(BaseModel):
    """Response from compliance check."""
    submission_id: int
    compliance_status: ComplianceStatus
    issues: list[dict] = []
    recommendations: list[str] = []
    score: int = Field(ge=0, le=100)
