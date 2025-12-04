from __future__ import annotations

from pgvector.sqlalchemy import Vector
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.config import settings
from app.core.database import Base
from app.models.mixins import TimestampMixin

EMBEDDING_DIM = settings.active_embedding_dim


class Embedding(Base, TimestampMixin):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Polymorphic owner reference: ("resume", id) or ("job", id)
    owner_type: Mapped[str] = mapped_column(String(32), index=True)
    owner_id: Mapped[int] = mapped_column(Integer, index=True)
    model: Mapped[str] = mapped_column(String(120))
    dim: Mapped[int] = mapped_column(Integer, default=EMBEDDING_DIM)
    vector: Mapped[list[float]] = mapped_column(Vector(EMBEDDING_DIM))
