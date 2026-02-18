"""Document management API endpoints."""
import os
import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from datetime import datetime

from ..core.database import get_db
from ..models.document import Document
from ..models.submission import Submission

router = APIRouter(prefix="/api/v1/submissions", tags=["documents"])

UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/{submission_id}/documents")
async def upload_document(
    submission_id: int,
    file: UploadFile = File(...),
    document_type: str = Form("supporting_doc"),
    db: Session = Depends(get_db)
):
    """Upload a supporting document for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    sub_dir = os.path.join(UPLOAD_DIR, str(submission_id))
    os.makedirs(sub_dir, exist_ok=True)

    file_ext = os.path.splitext(file.filename or "file")[1] or ".bin"
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(sub_dir, unique_filename)

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    doc = Document(
        submission_id=submission_id,
        document_type=document_type,
        filename=file.filename or unique_filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=file.content_type,
        uploaded_at=datetime.utcnow(),
        status="uploaded"
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "submission_id": doc.submission_id,
        "document_type": doc.document_type,
        "filename": doc.filename,
        "file_size": doc.file_size,
        "mime_type": doc.mime_type,
        "status": doc.status,
        "ai_reviewed": doc.ai_reviewed,
        "ai_review_summary": doc.ai_review_summary,
        "uploaded_at": doc.uploaded_at.isoformat()
    }


@router.get("/{submission_id}/documents")
async def list_documents(submission_id: int, db: Session = Depends(get_db)):
    """List all documents for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")

    docs = db.query(Document).filter(Document.submission_id == submission_id).all()
    return [
        {
            "id": d.id,
            "submission_id": d.submission_id,
            "document_type": d.document_type,
            "filename": d.filename,
            "file_size": d.file_size,
            "mime_type": d.mime_type,
            "status": d.status,
            "ai_reviewed": d.ai_reviewed,
            "ai_review_summary": d.ai_review_summary,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None
        }
        for d in docs
    ]


@router.delete("/{submission_id}/documents/{document_id}", status_code=204)
async def delete_document(submission_id: int, document_id: int, db: Session = Depends(get_db)):
    """Delete a document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.submission_id == submission_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    if os.path.exists(doc.file_path):
        os.remove(doc.file_path)

    db.delete(doc)
    db.commit()
    return None


@router.post("/{submission_id}/documents/{document_id}/ai-review")
async def ai_review_document(submission_id: int, document_id: int, db: Session = Depends(get_db)):
    """Trigger AI review of an uploaded document."""
    doc = db.query(Document).filter(
        Document.id == document_id,
        Document.submission_id == submission_id
    ).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        content = ""
        if doc.file_path and os.path.exists(doc.file_path):
            if doc.filename.lower().endswith(".pdf"):
                try:
                    import pdfplumber
                    with pdfplumber.open(doc.file_path) as pdf:
                        content = "\n".join(page.extract_text() or "" for page in pdf.pages[:10])
                except Exception:
                    content = f"[PDF document: {doc.filename}]"
            else:
                try:
                    with open(doc.file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read(10000)
                except Exception:
                    content = f"[Document: {doc.filename}]"

        if not content:
            content = f"[Document: {doc.filename}, Type: {doc.document_type}]"

        from ..agents.document_agent import document_agent
        prompt = f"""Analyze this {doc.document_type} document for FDA 510(k) submission relevance:

Document: {doc.filename}
Content: {content[:5000]}

Provide a concise summary with:
1. Key findings and data points
2. Regulatory relevance for FDA submission
3. Any gaps or concerns
4. How this supports the submission"""

        summary = await document_agent._call_claude(prompt, max_tokens=1000)

        doc.ai_reviewed = True
        doc.ai_review_summary = summary
        doc.status = "reviewed"
        db.commit()

        return {"status": "reviewed", "summary": summary}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI review failed: {str(e)}")
