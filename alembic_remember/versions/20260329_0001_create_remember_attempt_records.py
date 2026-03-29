"""create_remember_attempt_records

Revision ID: 20260329_0001_remember
Revises:
Create Date: 2026-03-29 18:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0001_remember"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "remember_attempt_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("public_id", sa.String(length=64), nullable=False),
        sa.Column("device_id", sa.String(length=128), nullable=False),
        sa.Column("nickname", sa.String(length=60), nullable=False),
        sa.Column("discipline", sa.String(length=20), nullable=False),
        sa.Column("difficulty_id", sa.String(length=20), nullable=False),
        sa.Column("difficulty_label", sa.String(length=60), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("accuracy", sa.Integer(), nullable=False),
        sa.Column("total_items", sa.Integer(), nullable=False),
        sa.Column("correct_items", sa.Integer(), nullable=False),
        sa.Column("summary", sa.String(length=255), nullable=True),
        sa.Column("achieved_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_remember_attempt_records_achieved_at"),
        "remember_attempt_records",
        ["achieved_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remember_attempt_records_device_id"),
        "remember_attempt_records",
        ["device_id"],
        unique=False,
    )
    op.create_index(
        "ix_remember_attempt_records_device_slot",
        "remember_attempt_records",
        ["device_id", "discipline", "difficulty_id", "achieved_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remember_attempt_records_difficulty_id"),
        "remember_attempt_records",
        ["difficulty_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remember_attempt_records_discipline"),
        "remember_attempt_records",
        ["discipline"],
        unique=False,
    )
    op.create_index(
        "ix_remember_attempt_records_event_slot",
        "remember_attempt_records",
        ["discipline", "difficulty_id", "achieved_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_remember_attempt_records_public_id"),
        "remember_attempt_records",
        ["public_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_remember_attempt_records_public_id"), table_name="remember_attempt_records")
    op.drop_index("ix_remember_attempt_records_event_slot", table_name="remember_attempt_records")
    op.drop_index(op.f("ix_remember_attempt_records_discipline"), table_name="remember_attempt_records")
    op.drop_index(op.f("ix_remember_attempt_records_difficulty_id"), table_name="remember_attempt_records")
    op.drop_index("ix_remember_attempt_records_device_slot", table_name="remember_attempt_records")
    op.drop_index(op.f("ix_remember_attempt_records_device_id"), table_name="remember_attempt_records")
    op.drop_index(op.f("ix_remember_attempt_records_achieved_at"), table_name="remember_attempt_records")
    op.drop_table("remember_attempt_records")
