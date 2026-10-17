"""create pantry_items table

Revision ID: 0001
Revises:
Create Date: 2026-10-17
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "pantry_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False, server_default="Other"),
        sa.Column("quantity", sa.Float(), nullable=False, server_default="1"),
        sa.Column("unit", sa.String(length=20), nullable=False, server_default="pcs"),
        sa.Column("expiry_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_pantry_items_id", "pantry_items", ["id"])
    op.create_index("ix_pantry_items_category", "pantry_items", ["category"])


def downgrade() -> None:
    op.drop_index("ix_pantry_items_category", table_name="pantry_items")
    op.drop_index("ix_pantry_items_id", table_name="pantry_items")
    op.drop_table("pantry_items")
