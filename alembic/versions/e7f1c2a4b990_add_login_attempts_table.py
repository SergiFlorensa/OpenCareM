"""add login_attempts table

Revision ID: e7f1c2a4b990
Revises: 9a3e5d4c2b11
Create Date: 2026-02-08 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e7f1c2a4b990"
down_revision: Union[str, None] = "9a3e5d4c2b11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Guarda intentos de login fallidos para aplicar
    # bloqueo temporal anti brute force.
    op.create_table(
        "login_attempts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("ip_address", sa.String(length=64), nullable=False),
        sa.Column("failed_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("first_failed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("blocked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_login_attempts_id"), "login_attempts", ["id"], unique=False)
    op.create_index(
        op.f("ix_login_attempts_ip_address"), "login_attempts", ["ip_address"], unique=False
    )
    op.create_index(
        op.f("ix_login_attempts_username"), "login_attempts", ["username"], unique=False
    )


def downgrade() -> None:
    # Elimina el control persistente de intentos y
    # vuelve al estado previo del esquema.
    op.drop_index(op.f("ix_login_attempts_username"), table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_ip_address"), table_name="login_attempts")
    op.drop_index(op.f("ix_login_attempts_id"), table_name="login_attempts")
    op.drop_table("login_attempts")
