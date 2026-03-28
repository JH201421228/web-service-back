"""expand_country_code_length

Revision ID: 20260329_0002
Revises: 20260329_0001
Create Date: 2026-03-29 03:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0002"
down_revision: Union[str, Sequence[str], None] = "20260329_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "tourist_country_snapshots",
        "country_code",
        existing_type=sa.String(length=2),
        type_=sa.String(length=3),
        existing_nullable=False,
    )


def downgrade() -> None:
    op.alter_column(
        "tourist_country_snapshots",
        "country_code",
        existing_type=sa.String(length=3),
        type_=sa.String(length=2),
        existing_nullable=False,
    )
