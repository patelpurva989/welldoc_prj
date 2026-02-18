"""RAG (Retrieval-Augmented Generation) Service for FDA Knowledge Base.

This service powers the semantic search layer that enriches AI-generated
510(k) submissions with relevant FDA regulatory guidance retrieved from
the vector database.

Design principles
-----------------
* If pgvector / Anthropic embeddings are unavailable the service degrades
  gracefully — generation still works, just without RAG augmentation.
* All vector operations are wrapped in try/except so a DB or API failure
  never blocks a submission generation request.
* Embedding dimension is fixed at 1 536 (OpenAI ada-002 compatible) so the
  same schema can be used with either provider.
"""
import logging
import math
import os
from typing import List, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal constants
# ---------------------------------------------------------------------------
EMBEDDING_DIM = 1536        # OpenAI ada-002 / Anthropic voyage compatible
_MAX_RAG_RESULTS = 5        # How many knowledge chunks to retrieve per query
_SIMILARITY_THRESHOLD = 0.65  # Minimum cosine similarity to include a chunk


# ---------------------------------------------------------------------------
# Embedding helpers
# ---------------------------------------------------------------------------

def _mock_embedding(text: str, dim: int = EMBEDDING_DIM) -> List[float]:
    """
    Produce a deterministic pseudo-embedding when no API key is configured.

    Uses character frequency hashing to create a normalised float vector.
    This allows the RAG pipeline to be exercised end-to-end in development
    and CI environments without hitting external APIs.

    NOTE: These mock embeddings have NO semantic meaning — they exist only
    so the database schema and retrieval plumbing can be tested locally.
    """
    # Build a hash-based frequency vector
    vec: List[float] = [0.0] * dim
    for i, ch in enumerate(text):
        idx = (ord(ch) * 31 + i) % dim
        vec[idx] += 1.0

    # L2 normalise
    magnitude = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / magnitude for v in vec]


async def embed_text(text: str) -> List[float]:
    """
    Generate a 1 536-dimensional embedding vector for *text*.

    Strategy
    --------
    1. If ``ANTHROPIC_API_KEY`` is set, use the Anthropic messages API with
       ``claude-3-haiku`` to get a surrogate embedding via a summarisation
       trick (Anthropic does not yet expose a dedicated embeddings endpoint;
       we therefore fall through to OpenAI if the key is present).
    2. If ``OPENAI_API_KEY`` is set, use ``text-embedding-ada-002``.
    3. Otherwise, return a deterministic mock embedding (no API cost, no
       semantic accuracy — development / CI only).

    Parameters
    ----------
    text:
        The text string to embed.  Will be truncated to 8 000 characters
        to avoid token-limit errors.

    Returns
    -------
    List[float]
        1 536-dimensional unit vector.
    """
    text = text[:8000]  # hard cap to stay within model context windows

    # --- Attempt OpenAI embeddings (ada-002 produces 1 536 dims) ---
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            from openai import OpenAI  # type: ignore
            client = OpenAI(api_key=openai_key)
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            embedding = response.data[0].embedding
            logger.debug("Embedded %d chars via OpenAI ada-002", len(text))
            return embedding
        except Exception as exc:
            logger.warning("OpenAI embedding failed (%s); falling back to mock", exc)

    # --- Fall back to deterministic mock embedding ---
    logger.info(
        "No embedding API key found — using mock embedding (dev/CI mode). "
        "Set OPENAI_API_KEY for production semantic search."
    )
    return _mock_embedding(text)


# ---------------------------------------------------------------------------
# CRUD operations
# ---------------------------------------------------------------------------

async def store_document(
    title: str,
    content: str,
    content_type: str,
    section: str,
    db: Session,
) -> "FDAKnowledgeBase":  # type: ignore[name-defined]  # noqa: F821
    """
    Store a knowledge-base document with its embedding.

    Parameters
    ----------
    title:        Short human-readable label.
    content:      Full guidance text.
    content_type: "guidance" | "predicate_summary" | "regulation"
    section:      Topic tag, e.g. "510k", "biocompatibility".
    db:           SQLAlchemy session.

    Returns
    -------
    FDAKnowledgeBase
        The newly persisted ORM instance.
    """
    from ..models.fda_knowledge import FDAKnowledgeBase

    embedding = await embed_text(f"{title} {content}")

    kb_entry = FDAKnowledgeBase(
        title=title,
        content=content,
        content_type=content_type,
        section=section,
        embedding=embedding,
    )
    db.add(kb_entry)
    db.commit()
    db.refresh(kb_entry)
    logger.info("Stored knowledge-base entry id=%d section=%s", kb_entry.id, section)
    return kb_entry


async def search_similar(
    query: str,
    limit: int = _MAX_RAG_RESULTS,
    db: Session = None,
    section_filter: Optional[str] = None,
) -> List["FDAKnowledgeBase"]:  # type: ignore[name-defined]  # noqa: F821
    """
    Retrieve the *limit* most semantically similar knowledge-base entries.

    Uses pgvector cosine-distance operator ``<=>`` when available, otherwise
    falls back to a Python-side dot-product ranking over all rows (suitable
    only for small knowledge bases in development).

    Parameters
    ----------
    query:          Natural-language query string.
    limit:          Maximum number of results to return.
    db:             SQLAlchemy session.
    section_filter: Optional topic tag to pre-filter results.

    Returns
    -------
    List[FDAKnowledgeBase]
        Ordered most-similar first.
    """
    from ..models.fda_knowledge import FDAKnowledgeBase

    if db is None:
        logger.warning("search_similar called without a DB session — returning empty list")
        return []

    query_embedding = await embed_text(query)

    # ---- Try pgvector native cosine similarity ----
    try:
        from pgvector.sqlalchemy import Vector  # noqa: F401
        import sqlalchemy as sa

        embedding_col = FDAKnowledgeBase.embedding
        q = db.query(FDAKnowledgeBase)

        if section_filter:
            q = q.filter(FDAKnowledgeBase.section == section_filter)

        # pgvector cosine distance (lower = more similar)
        results = (
            q.order_by(embedding_col.cosine_distance(query_embedding))
            .limit(limit)
            .all()
        )
        logger.debug(
            "pgvector search returned %d results for query=%r", len(results), query[:60]
        )
        return results

    except Exception as exc:
        logger.warning(
            "pgvector cosine search failed (%s); falling back to Python-side ranking",
            exc,
        )

    # ---- Python-side fallback (no pgvector) ----
    try:
        q = db.query(FDAKnowledgeBase)
        if section_filter:
            q = q.filter(FDAKnowledgeBase.section == section_filter)
        all_entries = q.all()

        if not all_entries:
            return []

        def _cosine_sim(a: List[float], b) -> float:
            """Compute cosine similarity; b may be a pgvector type or plain list."""
            if b is None:
                return 0.0
            b_list = list(b) if not isinstance(b, list) else b
            if len(a) != len(b_list):
                return 0.0
            dot = sum(x * y for x, y in zip(a, b_list))
            mag_a = math.sqrt(sum(x * x for x in a)) or 1.0
            mag_b = math.sqrt(sum(y * y for y in b_list)) or 1.0
            return dot / (mag_a * mag_b)

        scored = [
            (entry, _cosine_sim(query_embedding, entry.embedding))
            for entry in all_entries
        ]
        scored.sort(key=lambda t: t[1], reverse=True)
        return [entry for entry, score in scored[:limit] if score >= _SIMILARITY_THRESHOLD]

    except Exception as exc:
        logger.error("Python-side RAG fallback also failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# High-level RAG context builder
# ---------------------------------------------------------------------------

async def build_rag_context(submission, db: Session) -> str:
    """
    Build a structured RAG context string for a given submission.

    Runs two searches:
    1. A broad query based on the device description and indications.
    2. A 510(k)-specific query to surface relevant procedural guidance.

    The results are deduplicated, ranked, and formatted as a Markdown block
    ready to be appended to the generation prompt.

    Parameters
    ----------
    submission:
        A ``Submission`` ORM instance (needs .device_name,
        .device_description, .indications_for_use).
    db:
        Active SQLAlchemy session.

    Returns
    -------
    str
        Formatted RAG context block, or empty string if RAG is unavailable.
    """
    try:
        # Build search queries from submission fields
        device_query = (
            f"{submission.device_name or ''} "
            f"{submission.device_description or ''} "
            f"{submission.indications_for_use or ''}"
        ).strip()

        procedural_query = (
            f"510k premarket notification requirements substantial equivalence "
            f"{submission.device_name or ''}"
        )

        # Parallel retrieval (sequential here for simplicity; could be gathered)
        device_results = await search_similar(device_query, limit=3, db=db)
        procedural_results = await search_similar(procedural_query, limit=2, db=db)

        # Deduplicate by id
        seen_ids: set = set()
        combined: List["FDAKnowledgeBase"] = []  # type: ignore[name-defined]  # noqa: F821
        for entry in device_results + procedural_results:
            if entry.id not in seen_ids:
                seen_ids.add(entry.id)
                combined.append(entry)

        if not combined:
            logger.info(
                "RAG: no relevant guidance found for submission_id=%s",
                getattr(submission, "id", "?"),
            )
            return ""

        # Format as Markdown sections
        blocks: List[str] = []
        for entry in combined:
            blocks.append(
                f"### [{entry.content_type.upper()}] {entry.title}\n"
                f"*Section: {entry.section}*\n\n"
                f"{entry.content}"
            )

        rag_block = "\n\n---\n\n".join(blocks)
        logger.info(
            "RAG: built context from %d chunks (%d chars) for submission_id=%s",
            len(combined),
            len(rag_block),
            getattr(submission, "id", "?"),
        )
        return rag_block

    except Exception as exc:
        # RAG failure must never block generation
        logger.error(
            "RAG context build failed for submission_id=%s: %s",
            getattr(submission, "id", "?"),
            exc,
        )
        return ""
