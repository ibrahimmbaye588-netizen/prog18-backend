"""ajoute stock_deduit sur devis

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "devis",
        sa.Column("stock_deduit", sa.Boolean(), nullable=False, server_default="false"),
    )


def downgrade():
    op.drop_column("devis", "stock_deduit")
