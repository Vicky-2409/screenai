"""initial schema with pgvector

Revision ID: 0001_initial
Revises:
Create Date: 2026-06-26

This baseline enables the pgvector extension, creates all tables from the
SQLAlchemy metadata, and adds an ivfflat cosine index on the embeddings vector
column for fast semantic search.
"""
from __future__ import annotations

from alembic import op

from app.core.database import Base

# Import models so metadata is populated.
import app.models  # noqa: F401

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    # 1. Enable pgvector before creating any vector columns.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # 2. Create all tables defined on the SQLAlchemy metadata.
    Base.metadata.create_all(bind=bind)

    # 3. Approximate-nearest-neighbour index for semantic search.
    #    ivfflat works well for the dataset sizes targeted here; lists tuned for
    #    up to ~10k vectors. Cosine distance matches normalized embeddings.
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_embeddings_vector_cosine "
        "ON embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    bind = op.get_bind()
    op.execute("DROP INDEX IF EXISTS ix_embeddings_vector_cosine")
    Base.metadata.drop_all(bind=bind)
    op.execute("DROP EXTENSION IF EXISTS vector")
