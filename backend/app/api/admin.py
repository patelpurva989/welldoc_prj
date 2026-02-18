"""Admin API endpoints for internal management operations.

All endpoints under /api/v1/admin are intended for administrators only.
In production, protect this router with IP allow-listing or admin JWT middleware.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ..core.database import get_db
from ..models.fda_knowledge import FDAKnowledgeBase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ============================================================================
# RESPONSE SCHEMAS
# ============================================================================

class SeedKnowledgeBaseResponse(BaseModel):
    """Response for the seed-knowledge-base endpoint."""
    status: str
    entries_inserted: int
    total_entries: int
    message: str


class KnowledgeBaseStatsResponse(BaseModel):
    """Summary statistics for the knowledge base."""
    total_entries: int
    entries_by_section: dict
    entries_by_content_type: dict
    has_embeddings: int
    missing_embeddings: int


class DeleteKnowledgeBaseResponse(BaseModel):
    """Response after clearing the knowledge base."""
    status: str
    entries_deleted: int
    message: str


# ============================================================================
# SEED KNOWLEDGE BASE
# ============================================================================

@router.post(
    "/seed-knowledge-base",
    response_model=SeedKnowledgeBaseResponse,
    summary="Seed the FDA knowledge base with regulatory guidance",
    description=(
        "Populates the fda_knowledge_base table with curated FDA 510(k) regulatory "
        "guidance text and generates vector embeddings for each entry.  "
        "Returns 200 on success (new entries inserted). "
        "Returns 409 if the knowledge base is already seeded and ?force=false (default). "
        "Pass ?force=true to re-seed even when entries exist (deduplication by title)."
    ),
)
async def seed_knowledge_base(
    force: bool = Query(
        default=False,
        description=(
            "If true, re-seeds even when entries already exist. "
            "Deduplication is by title, so existing entries are never duplicated."
        ),
    ),
    db: Session = Depends(get_db),
):
    """
    Seed the FDA regulatory knowledge base.

    - On first run: inserts all curated guidance entries and computes embeddings.
      Returns HTTP 200 with entries_inserted > 0.
    - On subsequent runs without ?force=true: returns HTTP 409 (already seeded).
    - With ?force=true: runs full seed, skipping only exact title duplicates,
      returns HTTP 200 with entries_inserted >= 0.
    """
    try:
        from ..services.fda_knowledge_seeder import seed_fda_knowledge_base

        # When not forcing, check upfront so we can return 409
        if not force:
            existing_count = db.query(FDAKnowledgeBase).count()
            if existing_count > 0:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        f"Knowledge base already contains {existing_count} entries. "
                        "Use ?force=true to re-seed (existing titles are skipped)."
                    ),
                )

        inserted = await seed_fda_knowledge_base(db, skip_existing=not force)
        total = db.query(FDAKnowledgeBase).count()

        return SeedKnowledgeBaseResponse(
            status="success",
            entries_inserted=inserted,
            total_entries=total,
            message=(
                f"Knowledge base seeded: {inserted} new entries inserted. "
                f"Total entries in DB: {total}."
            ),
        )

    except HTTPException:
        raise  # Re-raise 409 and other intentional HTTP errors unchanged
    except Exception as exc:
        logger.error("seed-knowledge-base failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to seed knowledge base: {str(exc)}",
        )


# ============================================================================
# KNOWLEDGE BASE STATISTICS
# ============================================================================

@router.get(
    "/knowledge-base/stats",
    response_model=KnowledgeBaseStatsResponse,
    summary="Get FDA knowledge base statistics",
)
async def get_knowledge_base_stats(db: Session = Depends(get_db)):
    """Return summary statistics for the FDA knowledge base."""
    try:
        all_entries = db.query(FDAKnowledgeBase).all()
        total = len(all_entries)

        by_section: dict = {}
        by_content_type: dict = {}
        has_embeddings = 0
        missing_embeddings = 0

        for entry in all_entries:
            by_section[entry.section] = by_section.get(entry.section, 0) + 1
            by_content_type[entry.content_type] = (
                by_content_type.get(entry.content_type, 0) + 1
            )
            if entry.embedding is not None:
                has_embeddings += 1
            else:
                missing_embeddings += 1

        return KnowledgeBaseStatsResponse(
            total_entries=total,
            entries_by_section=by_section,
            entries_by_content_type=by_content_type,
            has_embeddings=has_embeddings,
            missing_embeddings=missing_embeddings,
        )

    except Exception as exc:
        logger.error("knowledge-base/stats failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve knowledge base stats: {str(exc)}",
        )


# ============================================================================
# LIST KNOWLEDGE BASE ENTRIES
# ============================================================================

@router.get(
    "/knowledge-base",
    summary="List FDA knowledge base entries",
)
async def list_knowledge_base(
    section: Optional[str] = Query(None, description="Filter by section tag"),
    content_type: Optional[str] = Query(None, description="Filter by content type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List knowledge base entries with optional filters (no embeddings returned)."""
    try:
        q = db.query(FDAKnowledgeBase)
        if section:
            q = q.filter(FDAKnowledgeBase.section == section)
        if content_type:
            q = q.filter(FDAKnowledgeBase.content_type == content_type)

        entries = q.order_by(FDAKnowledgeBase.id).offset(skip).limit(limit).all()
        total = q.count()

        return {
            "total": total,
            "skip": skip,
            "limit": limit,
            "entries": [
                {
                    "id": e.id,
                    "title": e.title,
                    "content_type": e.content_type,
                    "section": e.section,
                    "content_preview": e.content[:200] + "..." if len(e.content) > 200 else e.content,
                    "has_embedding": e.embedding is not None,
                    "created_at": e.created_at.isoformat() if e.created_at else None,
                }
                for e in entries
            ],
        }

    except Exception as exc:
        logger.error("knowledge-base list failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list knowledge base: {str(exc)}",
        )


# ============================================================================
# DELETE / RESET KNOWLEDGE BASE  (use with care)
# ============================================================================

@router.delete(
    "/knowledge-base",
    response_model=DeleteKnowledgeBaseResponse,
    summary="Clear the FDA knowledge base (admin only)",
)
async def delete_knowledge_base(db: Session = Depends(get_db)):
    """
    Delete all entries from the FDA knowledge base.
    Use this to reset before re-seeding with updated content.
    """
    try:
        count = db.query(FDAKnowledgeBase).count()
        db.query(FDAKnowledgeBase).delete()
        db.commit()
        logger.warning("FDA knowledge base cleared: %d entries deleted", count)
        return DeleteKnowledgeBaseResponse(
            status="success",
            entries_deleted=count,
            message=f"Deleted {count} entries from fda_knowledge_base.",
        )
    except Exception as exc:
        db.rollback()
        logger.error("knowledge-base delete failed: %s", exc)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear knowledge base: {str(exc)}",
        )
