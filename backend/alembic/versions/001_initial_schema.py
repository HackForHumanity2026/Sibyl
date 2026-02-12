"""Initial schema with pgvector extension and all 5 tables.

Revision ID: 001
Revises:
Create Date: 2026-02-11

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create pgvector extension and all tables."""
    # Enable pgvector extension
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create reports table
    op.create_table(
        "reports",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False, server_default="uploaded"),
        sa.Column("parsed_content", sa.Text(), nullable=True),
        sa.Column("pdf_binary", sa.LargeBinary(), nullable=True),
        sa.Column("content_structure", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_reports_status", "reports", ["status"])

    # Create claims table
    op.create_table(
        "claims",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("claim_type", sa.String(length=50), nullable=False),
        sa.Column("source_page", sa.Integer(), nullable=False),
        sa.Column("source_location", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("ifrs_paragraphs", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="medium"),
        sa.Column("agent_reasoning", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_claims_report_id", "claims", ["report_id"])
    op.create_index("ix_claims_claim_type", "claims", ["claim_type"])

    # Create findings table
    op.create_table(
        "findings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("claim_id", sa.UUID(), nullable=False),
        sa.Column("agent_name", sa.String(length=50), nullable=False),
        sa.Column("evidence_type", sa.String(length=50), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("details", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("supports_claim", sa.Boolean(), nullable=True),
        sa.Column("confidence", sa.String(length=20), nullable=True),
        sa.Column("iteration", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_findings_claim_id", "findings", ["claim_id"])
    op.create_index("ix_findings_agent_name", "findings", ["agent_name"])
    op.create_index("ix_findings_claim_id_agent_name", "findings", ["claim_id", "agent_name"])

    # Create verdicts table
    op.create_table(
        "verdicts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("claim_id", sa.UUID(), nullable=False),
        sa.Column("verdict", sa.String(length=30), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("ifrs_mapping", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("evidence_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("iteration_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["claim_id"], ["claims.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("claim_id"),
    )

    # Create embeddings table
    op.create_table(
        "embeddings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("report_id", sa.UUID(), nullable=True),
        sa.Column("source_type", sa.String(length=30), nullable=False),
        sa.Column("chunk_text", sa.Text(), nullable=False),
        sa.Column("chunk_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("ts_content", postgresql.TSVECTOR(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["report_id"], ["reports.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_embeddings_report_id", "embeddings", ["report_id"])
    op.create_index("ix_embeddings_source_type", "embeddings", ["source_type"])
    op.create_index(
        "ix_embeddings_embedding_hnsw",
        "embeddings",
        ["embedding"],
        postgresql_using="hnsw",
        postgresql_with={"m": 16, "ef_construction": 64},
        postgresql_ops={"embedding": "vector_cosine_ops"},
    )
    op.create_index(
        "ix_embeddings_ts_content_gin",
        "embeddings",
        ["ts_content"],
        postgresql_using="gin",
    )


def downgrade() -> None:
    """Drop all tables and pgvector extension."""
    op.drop_table("embeddings")
    op.drop_table("verdicts")
    op.drop_table("findings")
    op.drop_table("claims")
    op.drop_table("reports")
    op.execute("DROP EXTENSION IF EXISTS vector")
