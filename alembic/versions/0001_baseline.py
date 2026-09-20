"""Baseline : schéma de la phase 1, créé jusque-là par create_all.

Migration volontairement vide. Sur une base existante, on la « tamponne »
(alembic stamp 0001) au lieu de l'exécuter.

Revision ID: 0001
Revises:
"""
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
