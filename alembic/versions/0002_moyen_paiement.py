"""Ajoute moyen_paiement (especes, mobile_money, carte, virement, cheque) aux ventes et paiements.

Idempotente : sur une base neuve, create_all a déjà créé les colonnes.

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def _colonnes(table: str) -> set[str]:
    return {c["name"] for c in sa.inspect(op.get_bind()).get_columns(table)}


def upgrade() -> None:
    for table in ("ventes", "paiements"):
        if "moyen_paiement" not in _colonnes(table):
            op.add_column(
                table,
                sa.Column("moyen_paiement", sa.String(), nullable=False, server_default="especes"),
            )


def downgrade() -> None:
    for table in ("ventes", "paiements"):
        if "moyen_paiement" in _colonnes(table):
            op.drop_column(table, "moyen_paiement")
