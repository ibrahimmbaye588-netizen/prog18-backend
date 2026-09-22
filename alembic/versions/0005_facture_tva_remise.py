"""ajoute tva, remise, code article, prix conseille et bon de commande sur les factures

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-22
"""
from alembic import op
import sqlalchemy as sa

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("factures", sa.Column("bon_commande", sa.String(), nullable=True))

    op.add_column("lignes_facture", sa.Column("code_article", sa.String(), nullable=True))
    op.add_column("lignes_facture", sa.Column("prix_conseille", sa.Numeric(10, 2), nullable=True))
    op.add_column(
        "lignes_facture",
        sa.Column("taux_tva", sa.Numeric(5, 2), nullable=False, server_default="18"),
    )
    op.add_column(
        "lignes_facture",
        sa.Column("remise", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )


def downgrade():
    op.drop_column("lignes_facture", "remise")
    op.drop_column("lignes_facture", "taux_tva")
    op.drop_column("lignes_facture", "prix_conseille")
    op.drop_column("lignes_facture", "code_article")
    op.drop_column("factures", "bon_commande")
