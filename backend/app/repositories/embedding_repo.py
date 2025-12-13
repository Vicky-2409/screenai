from __future__ import annotations

from sqlalchemy import delete as sa_delete
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.embedding import Embedding


def upsert(db: Session, owner_type: str, owner_id: int, vector: list[float], model: str) -> Embedding:
    existing = db.execute(
        select(Embedding).where(
            Embedding.owner_type == owner_type, Embedding.owner_id == owner_id
        )
    ).scalar_one_or_none()
    if existing:
        existing.vector = vector
        existing.model = model
        existing.dim = len(vector)
    else:
        existing = Embedding(
            owner_type=owner_type,
            owner_id=owner_id,
            vector=vector,
            model=model,
            dim=len(vector),
        )
        db.add(existing)
    db.commit()
    db.refresh(existing)
    return existing


def get(db: Session, owner_type: str, owner_id: int) -> Embedding | None:
    return db.execute(
        select(Embedding).where(
            Embedding.owner_type == owner_type, Embedding.owner_id == owner_id
        )
    ).scalar_one_or_none()


def delete_for(db: Session, owner_type: str, owner_id: int) -> None:
    db.execute(
        sa_delete(Embedding).where(
            Embedding.owner_type == owner_type, Embedding.owner_id == owner_id
        )
    )
    db.commit()


def semantic_search_resume_ids(
    db: Session, query_vector: list[float], job_id: int | None, limit: int
) -> list[tuple[int, float]]:
    """Return (resume_id, distance) ordered by cosine distance using pgvector.

    Joins resume embeddings to optionally filter by job. Uses the ``<=>`` cosine
    distance operator backed by an ivfflat index for sub-second search.
    """
    from app.models.candidate import Candidate
    from app.models.resume import Resume

    distance = Embedding.vector.cosine_distance(query_vector).label("distance")
    stmt = (
        select(Resume.id, distance)
        .join(Embedding, (Embedding.owner_type == "resume") & (Embedding.owner_id == Resume.id))
        .join(Candidate, Candidate.resume_id == Resume.id)
    )
    if job_id is not None:
        stmt = stmt.where(Resume.job_id == job_id)
    stmt = stmt.order_by(distance).limit(limit)
    return [(row[0], float(row[1])) for row in db.execute(stmt).all()]
