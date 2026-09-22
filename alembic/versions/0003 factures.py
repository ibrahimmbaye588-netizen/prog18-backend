"""Ajoute les factures : tables factures, lignes_facture, paiements_facture.

Ne touche à aucune table existante. Idempotente : sur une base neuve,
create_all a déjà créé ces tables.

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def _table_existe(nom: str) -> bool:
    return nom in sa.inspect(op.get_bind()).get_table_names()


def upgrade() -> None:
    if not _table_existe("factures"):
        op.create_table(
            "factures",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "utilisateur_id",
                sa.Integer(),
                sa.ForeignKey("utilisateurs.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("numero", sa.String(), nullable=False, index=True),
            sa.Column("client_id", sa.Integer(), sa.ForeignKey("clients.id"), nullable=True),
            sa.Column("client_nom_libre", sa.String(), nullable=True),
            sa.Column("devis_id", sa.Integer(), sa.ForeignKey("devis.id"), nullable=True),
            sa.Column("vente_id", sa.Integer(), sa.ForeignKey("ventes.id"), nullable=True),
            sa.Column("statut", sa.String(), nullable=False, server_default="brouillon"),
            sa.Column("notes", sa.Text(), nullable=True),
            sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
            sa.Column(
                "modifie_le",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                onupdate=sa.func.now(),
            ),
        )
        op.create_unique_constraint(
            "uq_factures_utilisateur_numero", "factures", ["utilisateur_id", "numero"]
        )

    if not _table_existe("lignes_facture"):
        op.create_table(
            "lignes_facture",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "facture_id",
                sa.Integer(),
                sa.ForeignKey("factures.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("article_id", sa.Integer(), sa.ForeignKey("articles.id"), nullable=True),
            sa.Column("designation", sa.String(), nullable=False),
            sa.Column("quantite", sa.Integer(), nullable=False, server_default="1"),
            sa.Column("prix_unitaire", sa.Numeric(10, 2), nullable=False, server_default="0"),
        )

    if not _table_existe("paiements_facture"):
        op.create_table(
            "paiements_facture",
            sa.Column("id", sa.Integer(), primary_key=True, index=True),
            sa.Column(
                "utilisateur_id",
                sa.Integer(),
                sa.ForeignKey("utilisateurs.id"),
                nullable=False,
                index=True,
            ),
            sa.Column(
                "facture_id",
                sa.Integer(),
                sa.ForeignKey("factures.id"),
                nullable=False,
                index=True,
            ),
            sa.Column("montant", sa.Numeric(10, 2), nullable=False),
            sa.Column("moyen_paiement", sa.String(), nullable=False, server_default="especes"),
            sa.Column("motif", sa.String(), nullable=True),
            sa.Column("cree_le", sa.DateTime(timezone=True), server_default=sa.func.now()),
        )


def downgrade() -> None:
    if _table_existe("paiements_facture"):
        op.drop_table("paiements_facture")
    if _table_existe("lignes_facture"):
        op.drop_table("lignes_facture")
    if _table_existe("factures"):
        op.drop_constraint("uq_factures_utilisateur_numero", "factures", type_="unique")
        op.drop_table("factures")
