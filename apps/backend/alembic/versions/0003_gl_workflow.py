"""Store GL rows, mapping snapshots, journal lines and generated reports."""

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("gl_uploads", sa.Column("content_sha256", sa.String(64)))
    op.add_column("gl_uploads", sa.Column("accounts", JSONB))
    op.add_column("gl_uploads", sa.Column("mapping_snapshot", JSONB))
    op.add_column("adjustment_entries", sa.Column("lines", JSONB))
    op.add_column("adjustment_entries", sa.Column("created_by", sa.String(255)))
    op.create_table(
        "gl_mapping_rules",
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), primary_key=True),
        sa.Column("vas_code", sa.String(50), primary_key=True),
        sa.Column("ifrs_code", sa.String(100), nullable=False),
    )
    op.create_table(
        "gl_reports",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("upload_id", UUID, sa.ForeignKey("gl_uploads.id"), nullable=False),
        sa.Column("created_by", sa.String(255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column("snapshot", JSONB, nullable=False),
    )
    op.create_index("ix_gl_reports_tenant_id", "gl_reports", ["tenant_id"])


def downgrade() -> None:
    op.drop_table("gl_reports")
    op.drop_table("gl_mapping_rules")
    op.drop_column("adjustment_entries", "created_by")
    op.drop_column("adjustment_entries", "lines")
    op.drop_column("gl_uploads", "mapping_snapshot")
    op.drop_column("gl_uploads", "accounts")
    op.drop_column("gl_uploads", "content_sha256")
