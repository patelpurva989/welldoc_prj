"""FDA Regulatory API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid
import asyncio
import json

import logging

import anthropic as anthropic_sdk

from ..core.database import get_db
from ..core.config import settings
from ..models.submission import (
    Submission, SubmissionReview, AdverseEvent, PredicateDevice,
    SubmissionStatus, ComplianceStatus
)
from ..models.document import Document

logger = logging.getLogger(__name__)
from ..schemas.submission import (
    SubmissionCreate, SubmissionUpdate, SubmissionResponse,
    GenerateSubmissionRequest, GenerateSubmissionResponse,
    ReviewCreate, ReviewResponse,
    AdverseEventCreate, AdverseEventResponse,
    PredicateDeviceSearch, PredicateDeviceResponse,
    ComplianceCheckRequest, ComplianceCheckResponse
)
from ..agents.document_agent import document_agent
from ..agents.evidence_agent import evidence_agent
from ..agents.adverse_event_agent import adverse_event_agent
from ..agents.compliance_agent import compliance_agent

router = APIRouter(prefix="/api/v1/regulatory", tags=["regulatory"])


# ============================================================================
# SUBMISSION ENDPOINTS
# ============================================================================

@router.post("/submissions", response_model=SubmissionResponse, status_code=201)
async def create_submission(
    submission: SubmissionCreate,
    db: Session = Depends(get_db)
):
    """Create a new FDA submission."""
    db_submission = Submission(
        submission_type=submission.submission_type,
        device_name=submission.device_name,
        device_description=submission.device_description,
        manufacturer=submission.manufacturer,
        indications_for_use=submission.indications_for_use,
        predicate_device_name=submission.predicate_device_name,
        predicate_k_number=submission.predicate_k_number,
        clinical_data=submission.clinical_data,
        status=SubmissionStatus.DRAFT
    )

    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)

    return db_submission


@router.get("/submissions", response_model=List[SubmissionResponse])
async def list_submissions(
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """List all submissions."""
    query = db.query(Submission)

    if status:
        try:
            status_enum = SubmissionStatus(status)
            query = query.filter(Submission.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    submissions = query.offset(skip).limit(limit).all()
    return submissions


@router.get("/submissions/{submission_id}", response_model=SubmissionResponse)
async def get_submission(submission_id: int, db: Session = Depends(get_db)):
    """Get a specific submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    return submission


@router.patch("/submissions/{submission_id}", response_model=SubmissionResponse)
async def update_submission(
    submission_id: int,
    submission_update: SubmissionUpdate,
    db: Session = Depends(get_db)
):
    """Update a submission."""
    db_submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Update fields
    update_data = submission_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_submission, field, value)

    db_submission.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(db_submission)

    return db_submission


@router.delete("/submissions/{submission_id}", status_code=204)
async def delete_submission(submission_id: int, db: Session = Depends(get_db)):
    """Delete a submission."""
    db_submission = db.query(Submission).filter(Submission.id == submission_id).first()

    if not db_submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    db.delete(db_submission)
    db.commit()

    return None


# ============================================================================
# DOCUMENT GENERATION ENDPOINTS
# ============================================================================

@router.post("/generate-submission", response_model=GenerateSubmissionResponse)
async def generate_submission_document(
    request: GenerateSubmissionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Generate FDA submission documents using AI."""
    # Get submission
    submission = db.query(Submission).filter(Submission.id == request.submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Update status
    submission.status = SubmissionStatus.GENERATING
    db.commit()

    try:
        # Generate 510(k) submission
        predicate_data = None
        if submission.predicate_k_number:
            predicate_device = db.query(PredicateDevice).filter(
                PredicateDevice.k_number == submission.predicate_k_number
            ).first()

            if predicate_device:
                predicate_data = {
                    "k_number": predicate_device.k_number,
                    "name": predicate_device.device_name,
                    "manufacturer": predicate_device.manufacturer,
                    "indications": predicate_device.indications_for_use,
                    "technology": predicate_device.technological_characteristics
                }

        # Gather AI-reviewed supporting documents for this submission
        reviewed_documents = db.query(Document).filter(
            Document.submission_id == request.submission_id,
            Document.ai_reviewed == True  # noqa: E712
        ).all()

        supporting_docs_payload = []
        if reviewed_documents:
            logger.info(
                "Including %d AI-reviewed documents in submission generation for submission_id=%d",
                len(reviewed_documents), request.submission_id
            )
            for doc in reviewed_documents:
                supporting_docs_payload.append({
                    "document_type": doc.document_type,
                    "filename": doc.filename,
                    "ai_review_summary": doc.ai_review_summary or ""
                })
        else:
            logger.info(
                "No AI-reviewed documents found for submission_id=%d. "
                "Upload and review documents via POST /api/v1/documents/upload "
                "and POST /api/v1/documents/{id}/ai-review to enhance generation.",
                request.submission_id
            )

        # ── RAG: Retrieve relevant FDA guidance from vector knowledge base ──
        rag_context = ""
        try:
            from ..services.rag_service import build_rag_context
            rag_context = await build_rag_context(submission, db)
            if rag_context:
                logger.info(
                    "RAG context built (%d chars) for submission_id=%d",
                    len(rag_context), request.submission_id
                )
        except Exception as rag_exc:
            # RAG failure must never block generation — log and continue
            logger.warning(
                "RAG context build failed for submission_id=%d: %s",
                request.submission_id, rag_exc
            )

        generated_submission = await document_agent.generate_510k_submission(
            device_name=submission.device_name,
            device_description=submission.device_description or "",
            manufacturer=submission.manufacturer or "",
            indications_for_use=submission.indications_for_use or "",
            predicate_device=predicate_data,
            clinical_data=submission.clinical_data,
            supporting_documents=supporting_docs_payload if supporting_docs_payload else None,
            rag_context=rag_context or None
        )

        # Generate substantial equivalence analysis if predicate exists
        se_analysis = None
        if request.include_predicate_analysis and predicate_data:
            subject_data = {
                "name": submission.device_name,
                "description": submission.device_description,
                "indications": submission.indications_for_use,
                "technology": {}  # Would extract from submission
            }

            se_analysis = await document_agent.generate_substantial_equivalence_analysis(
                subject_device=subject_data,
                predicate_device=predicate_data
            )

        # Run compliance check
        compliance_result = await compliance_agent.check_submission_compliance(
            submission_data={
                "device_name": submission.device_name,
                "submission_type": submission.submission_type.value,
                "status": submission.status.value,
                "created_at": submission.created_at.isoformat()
            }
        )

        # Update submission
        submission.generated_submission = generated_submission
        submission.substantial_equivalence_analysis = se_analysis
        submission.compliance_status = ComplianceStatus.COMPLIANT if compliance_result["compliant"] else ComplianceStatus.NON_COMPLIANT
        submission.compliance_report = {
            "score": compliance_result["score"],
            "analysis": compliance_result["analysis"],
            "checked_at": datetime.utcnow().isoformat()
        }
        submission.status = SubmissionStatus.REVIEW_PENDING
        submission.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(submission)

        return GenerateSubmissionResponse(
            submission_id=submission.id,
            generated_submission=generated_submission,
            substantial_equivalence_analysis=se_analysis,
            compliance_check={
                "compliant": compliance_result["compliant"],
                "score": compliance_result["score"]
            },
            status="success"
        )

    except Exception as e:
        submission.status = SubmissionStatus.DRAFT
        db.commit()
        raise HTTPException(status_code=500, detail=f"Error generating submission: {str(e)}")


# ============================================================================
# STREAMING DOCUMENT GENERATION ENDPOINT
# ============================================================================

@router.post("/submissions/{submission_id}/generate-stream")
async def generate_submission_stream(
    submission_id: int,
    include_predicate_analysis: bool = True,
    db: Session = Depends(get_db)
):
    """
    Stream FDA submission generation in real-time via Server-Sent Events.

    The client receives a sequence of JSON event objects on a persistent HTTP
    connection (text/event-stream).  Event shapes:

        {"type": "started",   "message": str}
        {"type": "progress",  "percent": int, "message": str}
        {"type": "chunk",     "text": str}          # AI token stream
        {"type": "completed", "percent": 100, "submission_id": int}
        {"type": "error",     "message": str}
    """

    async def event_generator():
        """Yield SSE-formatted data frames as the document is built."""

        def sse(payload: dict) -> str:
            return f"data: {json.dumps(payload)}\n\n"

        try:
            # ── Phase 0: start ──────────────────────────────────────────────
            yield sse({"type": "started", "message": "Initialising generation pipeline..."})
            await asyncio.sleep(0.05)

            # ── Phase 1: load submission ────────────────────────────────────
            submission = db.query(Submission).filter(Submission.id == submission_id).first()
            if not submission:
                yield sse({"type": "error", "message": f"Submission {submission_id} not found."})
                return

            submission.status = SubmissionStatus.GENERATING
            db.commit()

            yield sse({"type": "progress", "percent": 8, "message": "Submission loaded. Fetching predicate device data..."})
            await asyncio.sleep(0.05)

            # ── Phase 2: predicate device ───────────────────────────────────
            predicate_data = None
            if submission.predicate_k_number:
                predicate_device = db.query(PredicateDevice).filter(
                    PredicateDevice.k_number == submission.predicate_k_number
                ).first()
                if predicate_device:
                    predicate_data = {
                        "k_number": predicate_device.k_number,
                        "name": predicate_device.device_name,
                        "manufacturer": predicate_device.manufacturer,
                        "indications": predicate_device.indications_for_use,
                        "technology": predicate_device.technological_characteristics,
                    }

            yield sse({"type": "progress", "percent": 20, "message": "Scanning uploaded and AI-reviewed documents..."})
            await asyncio.sleep(0.05)

            # ── Phase 3: reviewed documents ─────────────────────────────────
            reviewed_documents = db.query(Document).filter(
                Document.submission_id == submission_id,
                Document.ai_reviewed == True  # noqa: E712
            ).all()

            supporting_docs_payload = []
            for doc in reviewed_documents:
                supporting_docs_payload.append({
                    "document_type": doc.document_type,
                    "filename": doc.filename,
                    "ai_review_summary": doc.ai_review_summary or "",
                })

            if reviewed_documents:
                logger.info(
                    "Streaming: including %d AI-reviewed documents for submission_id=%d",
                    len(reviewed_documents), submission_id
                )

            # ── Phase 3b: RAG — retrieve relevant FDA guidance ──────────────
            yield sse({"type": "progress", "percent": 30, "message": "Retrieving relevant FDA regulatory guidance (RAG)..."})
            await asyncio.sleep(0.05)

            rag_context = ""
            try:
                from ..services.rag_service import build_rag_context as _build_rag_context
                rag_context = await _build_rag_context(submission, db)
                if rag_context:
                    logger.info(
                        "Streaming: RAG context built (%d chars) for submission_id=%d",
                        len(rag_context), submission_id,
                    )
            except Exception as rag_exc:
                logger.warning(
                    "Streaming: RAG context build failed for submission_id=%d: %s",
                    submission_id, rag_exc,
                )

            yield sse({"type": "progress", "percent": 35, "message": "Building 510(k) submission prompt..."})
            await asyncio.sleep(0.05)

            # ── Phase 4: build the generation prompt (mirrors document_agent) ─
            def fmt_predicate(p: dict) -> str:
                return (
                    f"\n- K-Number: {p.get('k_number', 'N/A')}"
                    f"\n- Device Name: {p.get('name', 'N/A')}"
                    f"\n- Manufacturer: {p.get('manufacturer', 'N/A')}"
                    f"\n- Indications: {p.get('indications', 'N/A')}\n"
                )

            def fmt_clinical(c: dict) -> str:
                if not c:
                    return "No clinical data provided"
                return "\n".join(f"- {k}: {v}" for k, v in c.items())

            prompt_parts = [
                "Generate a comprehensive 510(k) Premarket Notification submission "
                "for the following device:\n",
                "**Device Information:**",
                f"- Device Name: {submission.device_name}",
                f"- Manufacturer: {submission.manufacturer or 'Not specified'}",
                f"- Description: {submission.device_description or 'Not provided'}",
                f"- Indications for Use: {submission.indications_for_use or 'Not provided'}",
                "",
                "**Predicate Device:**",
                fmt_predicate(predicate_data) if predicate_data else "No predicate device specified",
                "",
                "**Clinical Data:**",
                fmt_clinical(submission.clinical_data) if submission.clinical_data else "No clinical data provided",
            ]

            if supporting_docs_payload:
                prompt_parts += [
                    "",
                    "### SUPPORTING DOCUMENTS (AI-Reviewed):",
                    (
                        "The following documents were uploaded by the regulatory team and "
                        "reviewed by AI. Incorporate their key findings into the relevant "
                        "sections of the submission.\n"
                    ),
                ]
                for idx, doc in enumerate(supporting_docs_payload, start=1):
                    prompt_parts.append(
                        f"**Document {idx}: {doc['document_type']}** (File: {doc['filename']})\n"
                        f"{doc['ai_review_summary']}\n"
                    )

            # Append RAG context if available
            if rag_context:
                prompt_parts += [
                    "",
                    "## RELEVANT FDA REGULATORY GUIDANCE (Retrieved from Knowledge Base):",
                    "The following regulatory guidance has been retrieved to help ensure "
                    "this submission meets current FDA standards. Incorporate applicable "
                    "requirements into the relevant sections below.",
                    "",
                    rag_context,
                ]

            prompt_parts += [
                "",
                "Generate a complete submission document with the following sections:",
                "1. EXECUTIVE SUMMARY",
                "2. DEVICE DESCRIPTION",
                "3. INDICATIONS FOR USE",
                "4. TECHNOLOGICAL CHARACTERISTICS",
                "5. PERFORMANCE TESTING",
                "6. SUBSTANTIAL EQUIVALENCE COMPARISON",
                "7. CLINICAL SUMMARY (if applicable)",
                "8. LABELING",
                "9. CONCLUSION",
                "",
                "Each section should be comprehensive, professionally written, and FDA-compliant.",
            ]

            full_prompt = "\n".join(prompt_parts)

            system_prompt = (
                "You are an FDA regulatory affairs expert specializing in medical device submissions. "
                "Generate comprehensive, compliant 510(k) premarket notification submissions. "
                "Use clear section headers, professional regulatory language, and follow 21 CFR Part 807."
            )

            yield sse({"type": "progress", "percent": 45, "message": "Connecting to Claude AI and starting generation..."})
            await asyncio.sleep(0.05)

            # ── Phase 5: stream from Anthropic ──────────────────────────────
            client = anthropic_sdk.AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
            full_text_chunks: list[str] = []

            async with client.messages.stream(
                model=settings.CLAUDE_MODEL,
                max_tokens=8192,
                system=system_prompt,
                messages=[{"role": "user", "content": full_prompt}],
            ) as stream:
                async for text_chunk in stream.text_stream:
                    full_text_chunks.append(text_chunk)
                    yield sse({"type": "chunk", "text": text_chunk})

            generated_submission = "".join(full_text_chunks)

            yield sse({"type": "progress", "percent": 80, "message": "AI generation complete. Running compliance check..."})
            await asyncio.sleep(0.05)

            # ── Phase 6: compliance check (reuse existing agent) ────────────
            compliance_result = await compliance_agent.check_submission_compliance(
                submission_data={
                    "device_name": submission.device_name,
                    "submission_type": submission.submission_type.value,
                    "status": submission.status.value,
                    "created_at": submission.created_at.isoformat(),
                }
            )

            yield sse({"type": "progress", "percent": 90, "message": "Saving generated document to database..."})
            await asyncio.sleep(0.05)

            # ── Phase 7: optional substantial equivalence analysis ──────────
            se_analysis = None
            if include_predicate_analysis and predicate_data:
                subject_data = {
                    "name": submission.device_name,
                    "description": submission.device_description,
                    "indications": submission.indications_for_use,
                    "technology": {},
                }
                se_analysis = await document_agent.generate_substantial_equivalence_analysis(
                    subject_device=subject_data,
                    predicate_device=predicate_data,
                )

            # ── Phase 8: persist ────────────────────────────────────────────
            submission.generated_submission = generated_submission
            submission.substantial_equivalence_analysis = se_analysis
            submission.compliance_status = (
                ComplianceStatus.COMPLIANT
                if compliance_result["compliant"]
                else ComplianceStatus.NON_COMPLIANT
            )
            submission.compliance_report = {
                "score": compliance_result["score"],
                "analysis": compliance_result["analysis"],
                "checked_at": datetime.utcnow().isoformat(),
            }
            submission.status = SubmissionStatus.REVIEW_PENDING
            submission.updated_at = datetime.utcnow()
            db.commit()

            yield sse({
                "type": "completed",
                "percent": 100,
                "submission_id": submission_id,
                "compliance_score": compliance_result["score"],
                "compliant": compliance_result["compliant"],
                "message": "510(k) submission generated and saved successfully.",
            })

        except Exception as exc:
            logger.exception("Streaming generation failed for submission_id=%d", submission_id)
            # Best-effort rollback
            try:
                submission_obj = db.query(Submission).filter(Submission.id == submission_id).first()
                if submission_obj and submission_obj.status == SubmissionStatus.GENERATING:
                    submission_obj.status = SubmissionStatus.DRAFT
                    db.commit()
            except Exception:
                pass
            yield sse({"type": "error", "message": str(exc)})

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        },
    )


# ============================================================================
# REVIEW ENDPOINTS (Human-in-the-Loop)
# ============================================================================

@router.post("/reviews", response_model=ReviewResponse, status_code=201)
async def create_review(review: ReviewCreate, db: Session = Depends(get_db)):
    """Submit a review for a submission (HITL)."""
    # Verify submission exists
    submission = db.query(Submission).filter(Submission.id == review.submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    db_review = SubmissionReview(
        submission_id=review.submission_id,
        reviewer_name=review.reviewer_name,
        reviewer_email=review.reviewer_email,
        section_reviewed=review.section_reviewed,
        comments=review.comments,
        suggested_changes=review.suggested_changes,
        approved=review.approved,
        reviewed_at=datetime.utcnow()
    )

    db.add(db_review)

    # Update submission status based on review
    if review.approved == 1:
        # Check if all sections approved
        all_reviews = db.query(SubmissionReview).filter(
            SubmissionReview.submission_id == review.submission_id
        ).all()

        if all(r.approved == 1 for r in all_reviews):
            submission.status = SubmissionStatus.APPROVED
    elif review.approved == -1:
        submission.status = SubmissionStatus.REJECTED

    db.commit()
    db.refresh(db_review)

    return db_review


@router.get("/submissions/{submission_id}/reviews", response_model=List[ReviewResponse])
async def get_submission_reviews(submission_id: int, db: Session = Depends(get_db)):
    """Get all reviews for a submission."""
    reviews = db.query(SubmissionReview).filter(
        SubmissionReview.submission_id == submission_id
    ).all()

    return reviews


# ============================================================================
# ADVERSE EVENT ENDPOINTS
# ============================================================================

@router.post("/adverse-events", response_model=AdverseEventResponse, status_code=201)
async def create_adverse_event(
    event: AdverseEventCreate,
    db: Session = Depends(get_db)
):
    """Report an adverse event."""
    # Generate analysis using AI
    analysis_result = await adverse_event_agent.analyze_adverse_event({
        "device_name": event.device_name,
        "event_type": event.event_type,
        "severity": event.severity,
        "description": event.description,
        "patient_age": event.patient_age,
        "patient_sex": event.patient_sex,
        "event_date": event.event_date.isoformat() if event.event_date else None
    })

    db_event = AdverseEvent(
        submission_id=event.submission_id,
        event_id=str(uuid.uuid4()),
        device_name=event.device_name,
        event_type=event.event_type,
        severity=event.severity,
        description=event.description,
        patient_age=event.patient_age,
        patient_sex=event.patient_sex,
        event_date=event.event_date,
        reported_date=datetime.utcnow(),
        ai_analysis=analysis_result["analysis"],
        risk_score=analysis_result["risk_score"]
    )

    db.add(db_event)
    db.commit()
    db.refresh(db_event)

    return db_event


@router.get("/adverse-events", response_model=List[AdverseEventResponse])
async def list_adverse_events(
    device_name: str = None,
    min_risk_score: int = 0,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List adverse events with optional filters."""
    query = db.query(AdverseEvent)

    if device_name:
        query = query.filter(AdverseEvent.device_name.ilike(f"%{device_name}%"))

    if min_risk_score:
        query = query.filter(AdverseEvent.risk_score >= min_risk_score)

    events = query.order_by(AdverseEvent.risk_score.desc()).offset(skip).limit(limit).all()

    return events


@router.get("/adverse-events/monitor/{device_name}")
async def monitor_faers(device_name: str, db: Session = Depends(get_db)):
    """Monitor FAERS database for device-related adverse events."""
    try:
        events = await adverse_event_agent.monitor_faers_database(device_name)

        # Save new events to database
        saved_count = 0
        for event_data in events:
            # Check if event already exists
            existing = db.query(AdverseEvent).filter(
                AdverseEvent.event_id == event_data["event_id"]
            ).first()

            if not existing:
                # Analyze event
                analysis_result = await adverse_event_agent.analyze_adverse_event(event_data)

                db_event = AdverseEvent(
                    event_id=event_data["event_id"],
                    device_name=event_data["device_name"],
                    event_type=event_data["event_type"],
                    severity=event_data["severity"],
                    description=event_data["description"],
                    patient_age=event_data.get("patient_age"),
                    patient_sex=event_data.get("patient_sex"),
                    reported_date=datetime.utcnow(),
                    ai_analysis=analysis_result["analysis"],
                    risk_score=analysis_result["risk_score"]
                )

                db.add(db_event)
                saved_count += 1

        db.commit()

        return {
            "device_name": device_name,
            "events_found": len(events),
            "new_events_saved": saved_count,
            "message": f"Monitoring complete. Found {len(events)} events, saved {saved_count} new events."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error monitoring FAERS: {str(e)}")


# ============================================================================
# PREDICATE DEVICE ENDPOINTS
# ============================================================================

@router.get("/predicate-devices", response_model=List[PredicateDeviceResponse])
async def search_predicate_devices(
    device_name: str = None,
    product_code: str = None,
    device_class: str = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search for predicate devices."""
    query = db.query(PredicateDevice)

    if device_name:
        query = query.filter(PredicateDevice.device_name.ilike(f"%{device_name}%"))

    if product_code:
        query = query.filter(PredicateDevice.product_code == product_code)

    if device_class:
        query = query.filter(PredicateDevice.device_class == device_class)

    devices = query.offset(skip).limit(limit).all()

    return devices


@router.get("/predicate-devices/{k_number}", response_model=PredicateDeviceResponse)
async def get_predicate_device(k_number: str, db: Session = Depends(get_db)):
    """Get predicate device by K number."""
    device = db.query(PredicateDevice).filter(PredicateDevice.k_number == k_number).first()

    if not device:
        raise HTTPException(status_code=404, detail="Predicate device not found")

    return device


# ============================================================================
# COMPLIANCE ENDPOINTS
# ============================================================================

@router.post("/compliance/check", response_model=ComplianceCheckResponse)
async def check_compliance(
    request: ComplianceCheckRequest,
    db: Session = Depends(get_db)
):
    """Perform 21 CFR Part 11 compliance check."""
    submission = db.query(Submission).filter(Submission.id == request.submission_id).first()

    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    # Perform compliance check
    result = await compliance_agent.check_submission_compliance(
        submission_data={
            "device_name": submission.device_name,
            "submission_type": submission.submission_type.value,
            "status": submission.status.value,
            "created_at": submission.created_at.isoformat(),
            "updated_at": submission.updated_at.isoformat()
        },
        check_electronic_signatures=request.check_electronic_signatures,
        check_audit_trail=request.check_audit_trail,
        check_record_retention=request.check_record_retention
    )

    # Update submission compliance status
    compliance_status = ComplianceStatus.COMPLIANT if result["compliant"] else ComplianceStatus.NON_COMPLIANT
    submission.compliance_status = compliance_status
    submission.compliance_report = {
        "score": result["score"],
        "analysis": result["analysis"],
        "checked_at": datetime.utcnow().isoformat()
    }

    db.commit()

    # Parse issues and recommendations from analysis
    # (In production, the agent would return structured data)
    issues = []
    recommendations = []

    return ComplianceCheckResponse(
        submission_id=request.submission_id,
        compliance_status=compliance_status,
        issues=issues,
        recommendations=recommendations,
        score=result["score"]
    )


@router.get("/compliance/checklist/{submission_type}")
async def get_compliance_checklist(submission_type: str):
    """Get compliance checklist for submission type."""
    try:
        checklist = await compliance_agent.generate_compliance_checklist(submission_type)

        return {
            "submission_type": submission_type,
            "checklist": checklist
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating checklist: {str(e)}")


# ============================================================================
# RAG — SIMILAR SUBMISSIONS / KNOWLEDGE SEARCH ENDPOINT
# ============================================================================

@router.get(
    "/similar-submissions",
    summary="Find similar FDA regulatory guidance using vector search",
    description=(
        "Searches the FDA knowledge base for regulatory guidance most semantically "
        "similar to the provided device description query. "
        "Useful for finding relevant 510(k) requirements, standards, and precedents "
        "before drafting a submission. "
        "Requires the knowledge base to be seeded via POST /api/v1/admin/seed-knowledge-base."
    ),
)
async def search_similar_submissions(
    q: str = Query(
        ...,
        min_length=3,
        description=(
            "Natural-language description of the device or regulatory topic to search for. "
            "Example: 'glucose monitor blood glucose measurement Class II'"
        ),
    ),
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of similar guidance entries to return.",
    ),
    section: Optional[str] = Query(
        default=None,
        description=(
            "Optionally filter results to a specific FDA topic section. "
            "Allowed values: 510k, biocompatibility, software, risk_management, "
            "labeling, performance_testing, sterilization, clinical_data, general"
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Semantic search over the FDA regulatory knowledge base.

    Returns the most relevant regulatory guidance entries for the query,
    ranked by cosine similarity of their vector embeddings.

    Response fields per entry:
    - id: knowledge base entry ID
    - title: short label
    - content_type: "guidance" | "predicate_summary" | "regulation"
    - section: FDA topic area
    - content_preview: first 400 characters of the guidance text
    - content: full guidance text
    """
    try:
        from ..services.rag_service import search_similar

        results = await search_similar(
            query=q,
            limit=limit,
            db=db,
            section_filter=section,
        )

        if not results:
            return {
                "query": q,
                "section_filter": section,
                "total_results": 0,
                "results": [],
                "message": (
                    "No similar regulatory guidance found. "
                    "Ensure the knowledge base is seeded via "
                    "POST /api/v1/admin/seed-knowledge-base."
                ),
            }

        return {
            "query": q,
            "section_filter": section,
            "total_results": len(results),
            "results": [
                {
                    "id": entry.id,
                    "title": entry.title,
                    "content_type": entry.content_type,
                    "section": entry.section,
                    "content_preview": entry.content[:400] + "..." if len(entry.content) > 400 else entry.content,
                    "content": entry.content,
                    "created_at": entry.created_at.isoformat() if entry.created_at else None,
                }
                for entry in results
            ],
        }

    except Exception as exc:
        logger.error("similar-submissions search failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Vector search failed: {str(exc)}",
        )
