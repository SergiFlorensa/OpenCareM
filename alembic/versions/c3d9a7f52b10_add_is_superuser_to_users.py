"""add is_superuser to users

Revision ID: c3d9a7f52b10
Revises: 74e6f2319a21
Create Date: 2026-02-07 20:05:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d9a7f52b10"
down_revision: Union[str, None] = "74e6f2319a21"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Añade bandera de administrador para distinguir usuarios con permisos altos.
    op.add_column(
        "users",
        sa.Column("is_superuser", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade() -> None:
    # Revierte la columna de administrador y vuelve al esquema anterior.
    op.drop_column("users", "is_superuser")
