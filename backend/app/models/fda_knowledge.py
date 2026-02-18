"""FDA Knowledge Base model for RAG (Retrieval-Augmented Generation).

Stores FDA regulatory guidance documents as vector embeddings to enable
semantic similarity search during submission generation.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from ..core.database import Base

# pgvector integration — imported lazily so the app can still start
# if pgvector is not yet installed (graceful degradation).
try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_TYPE = Vector(1536)          # OpenAI ada-002 / Anthropic compatible dimension
    _PGVECTOR_AVAILABLE = True
except ImportError:  # pragma: no cover
    # Fallback: store embeddings as JSON text when pgvector is unavailable
    from sqlalchemy import Text as _TextFallback
    _VECTOR_TYPE = _TextFallback()
    _PGVECTOR_AVAILABLE = False


class FDAKnowledgeBase(Base):
    """
    FDA Regulatory Knowledge Base entry.

    Each row represents a chunk of FDA regulatory guidance text along with
    its vector embedding.  The embedding is used for cosine-similarity
    searches to retrieve the most relevant guidance snippets for a given
    device submission query.

    Columns
    -------
    id            : auto-increment primary key
    title         : short human-readable label (e.g., "ISO 10993 Biocompatibility")
    content       : the full guidance text chunk (~500–1 500 words)
    content_type  : category bucket — one of:
                      "guidance"          – FDA guidance document excerpt
                      "predicate_summary" – summary of a predicate 510(k) decision
                      "regulation"        – CFR regulation text
    section       : high-level topic tag — one of:
                      "510k", "biocompatibility", "software", "risk_management",
                      "labeling", "performance_testing", "sterilization",
                      "clinical_data", "general"
    embedding     : 1536-dimensional float vector (pgvector)
    created_at    : insertion timestamp
    """
    __tablename__ = "fda_knowledge_base"

    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="guidance")
    section = Column(String(100), nullable=False, default="general")
    embedding = Column(_VECTOR_TYPE, nullable=True)   # nullable for non-pgvector fallback
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return (
            f"<FDAKnowledgeBase id={self.id!r} section={self.section!r} "
            f"title={self.title[:60]!r}>"
        )
