"""Review management API endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from pydantic import BaseModel

from ..core.database import get_db
from ..models.review import Review, ReviewChecklistItem, SubmissionStatusLog
from ..models.submission import Submission

router = APIRouter(prefix="/api/v1/submissions", tags=["reviews"])

FDA_SECTIONS = [
    (1, "Medical Device User Fee Cover Sheet"),
    (2, "CDRH Premarket Review Submission Cover Sheet"),
    (3, "Cover Letter"),
    (4, "Table of Contents"),
    (5, "Indications for Use Statement"),
    (6, "Device Description"),
    (7, "Predicate Device Information"),
    (8, "Substantial Equivalence Rationale"),
    (9, "Performance Data/Test Reports"),
    (10, "Biocompatibility Documentation"),
    (11, "Sterilization Information"),
    (12, "Software Documentation"),
    (13, "Risk Management"),
    (14, "Manufacturing Information"),
    (15, "Labeling"),
    (16, "Quality Systems"),
    (17, "Clinical Data"),
    (18, "Literature Review"),
    (19, "Patent Information"),
    (20, "Additional Information"),
]


class ReviewCreate(BaseModel):
    reviewer_name: Optional[str] = "Reviewer"
    review_round: Optional[int] = 1
    overall_notes: Optional[str] = None


class ChecklistItemUpdate(BaseModel):
    is_complete: Optional[bool] = None
    is_applicable: Optional[bool] = None
    completeness_percent: Optional[int] = None
    deficiency_level: Optional[str] = None
    reviewer_notes: Optional[str] = None
    assignee: Optional[str] = None


class ReviewStatusUpdate(BaseModel):
    status: str
    overall_notes: Optional[str] = None


def review_to_dict(review):
    return {
        "id": review.id,
        "submission_id": review.submission_id,
        "reviewer_name": review.reviewer_name,
        "review_round": review.review_round,
        "status": review.status,
        "overall_notes": review.overall_notes,
        "started_at": review.started_at.isoformat() if review.started_at else None,
        "completed_at": review.completed_at.isoformat() if review.completed_at else None,
        "created_at": review.created_at.isoformat() if review.created_at else None,
    }


def checklist_to_dict(item):
    return {
        "id": item.id,
        "review_id": item.review_id,
        "section_number": item.section_number,
        "section_name": item.section_name,
        "is_complete": item.is_complete,
        "is_applicable": item.is_applicable,
        "completeness_percent": item.completeness_percent,
        "deficiency_level": item.deficiency_level,
        "reviewer_notes": item.reviewer_notes,
        "assignee": item.assignee,
        "checked_at": item.checked_at.isoformat() if item.checked_at else None,
    }


@router.post("/{submission_id}/reviews")
async def create_review(submission_id: int, body: ReviewCreate, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    review = Review(
        submission_id=submission_id,
        reviewer_name=body.reviewer_name,
        review_round=body.review_round,
        status="in_progress",
        started_at=datetime.utcnow(),
        overall_notes=body.overall_notes,
    )
    db.add(review)
    db.flush()

    for section_num, section_name in FDA_SECTIONS:
        db.add(ReviewChecklistItem(
            review_id=review.id,
            section_number=section_num,
            section_name=section_name,
            is_complete=False,
            is_applicable=True,
            completeness_percent=0,
        ))

    db.commit()
    db.refresh(review)
    return review_to_dict(review)


@router.get("/{submission_id}/reviews")
async def list_reviews(submission_id: int, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    reviews = db.query(Review).filter(Review.submission_id == submission_id).all()
    return [review_to_dict(r) for r in reviews]


@router.get("/{submission_id}/reviews/{review_id}")
async def get_review(submission_id: int, review_id: int, db: Session = Depends(get_db)):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.submission_id == submission_id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    result = review_to_dict(review)
    result["checklist"] = [checklist_to_dict(item) for item in review.checklist_items]
    applicable = [i for i in review.checklist_items if i.is_applicable]
    result["overall_progress"] = (sum(i.completeness_percent for i in applicable) // len(applicable)) if applicable else 0
    return result


@router.patch("/{submission_id}/reviews/{review_id}/checklist/{item_id}")
async def update_checklist_item(
    submission_id: int, review_id: int, item_id: int,
    body: ChecklistItemUpdate, db: Session = Depends(get_db)
):
    item = db.query(ReviewChecklistItem).filter(
        ReviewChecklistItem.id == item_id,
        ReviewChecklistItem.review_id == review_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    if body.is_complete is True:
        item.checked_at = datetime.utcnow()
        if body.completeness_percent is None:
            item.completeness_percent = 100
    item.updated_at = datetime.utcnow()

    review = db.query(Review).filter(Review.id == review_id).first()
    if review:
        applicable = [i for i in review.checklist_items if i.is_applicable]
        if applicable:
            progress = sum(i.completeness_percent for i in applicable) // len(applicable)
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if submission and hasattr(submission, "progress_percent"):
                submission.progress_percent = progress

    db.commit()
    db.refresh(item)
    return checklist_to_dict(item)


@router.patch("/{submission_id}/reviews/{review_id}")
async def update_review(
    submission_id: int, review_id: int,
    body: ReviewStatusUpdate, db: Session = Depends(get_db)
):
    review = db.query(Review).filter(
        Review.id == review_id,
        Review.submission_id == submission_id
    ).first()
    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    prev_status = review.status
    review.status = body.status
    if body.overall_notes:
        review.overall_notes = body.overall_notes
    if body.status in ("completed", "approved", "rejected"):
        review.completed_at = datetime.utcnow()

    db.add(SubmissionStatusLog(
        submission_id=submission_id,
        previous_status=prev_status,
        new_status=body.status,
        changed_by="reviewer",
        notes=body.overall_notes,
    ))
    db.commit()
    db.refresh(review)
    return review_to_dict(review)


@router.get("/{submission_id}/status-history")
async def get_status_history(submission_id: int, db: Session = Depends(get_db)):
    logs = db.query(SubmissionStatusLog).filter(
        SubmissionStatusLog.submission_id == submission_id
    ).order_by(SubmissionStatusLog.changed_at.desc()).all()
    return [
        {
            "id": log.id,
            "previous_status": log.previous_status,
            "new_status": log.new_status,
            "changed_by": log.changed_by,
            "notes": log.notes,
            "changed_at": log.changed_at.isoformat() if log.changed_at else None,
        }
        for log in logs
    ]
