"""Add report_id to findings and verdicts tables.

The FRD 5 implementation added report_id foreign keys to the Finding and
Verdict models, but no migration was included. This migration adds the
missing columns, populates them from the existing claim -> report relationship,
and creates the required indexes.

Revision ID: 002
Revises: 001
Create Date: 2026-02-15

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add report_id columns to findings and verdicts."""
    # --- findings ---
    # 1. Add column as nullable first
    op.add_column(
        "findings",
        sa.Column("report_id", sa.UUID(), nullable=True),
    )

    # 2. Backfill from claims.report_id for existing rows
    op.execute(
        """
        UPDATE findings
        SET report_id = claims.report_id
        FROM claims
        WHERE findings.claim_id = claims.id
        """
    )

    # 3. Make claim_id nullable (model changed to nullable=True for report-level findings)
    op.alter_column("findings", "claim_id", existing_type=sa.UUID(), nullable=True)

    # 4. Set NOT NULL now that data is backfilled
    op.alter_column("findings", "report_id", existing_type=sa.UUID(), nullable=False)

    # 5. Add foreign key constraint
    op.create_foreign_key(
        "fk_findings_report_id",
        "findings",
        "reports",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 6. Add index
    op.create_index("ix_findings_report_id", "findings", ["report_id"])

    # --- verdicts ---
    # 1. Add column as nullable first
    op.add_column(
        "verdicts",
        sa.Column("report_id", sa.UUID(), nullable=True),
    )

    # 2. Backfill from claims.report_id for existing rows
    op.execute(
        """
        UPDATE verdicts
        SET report_id = claims.report_id
        FROM claims
        WHERE verdicts.claim_id = claims.id
        """
    )

    # 3. Set NOT NULL now that data is backfilled
    op.alter_column("verdicts", "report_id", existing_type=sa.UUID(), nullable=False)

    # 4. Add foreign key constraint
    op.create_foreign_key(
        "fk_verdicts_report_id",
        "verdicts",
        "reports",
        ["report_id"],
        ["id"],
        ondelete="CASCADE",
    )

    # 5. Add index
    op.create_index("ix_verdicts_report_id", "verdicts", ["report_id"])


def downgrade() -> None:
    """Remove report_id columns from findings and verdicts."""
    # --- verdicts ---
    op.drop_index("ix_verdicts_report_id", table_name="verdicts")
    op.drop_constraint("fk_verdicts_report_id", "verdicts", type_="foreignkey")
    op.drop_column("verdicts", "report_id")

    # --- findings ---
    op.drop_index("ix_findings_report_id", table_name="findings")
    op.drop_constraint("fk_findings_report_id", "findings", type_="foreignkey")
    op.alter_column("findings", "claim_id", existing_type=sa.UUID(), nullable=False)
    op.drop_column("findings", "report_id")
