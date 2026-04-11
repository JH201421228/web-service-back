"""drop reaper game events

Revision ID: 20260412_0002
Revises: 20260412_0001
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260412_0002"
down_revision = "20260412_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("reaper_game_events")


def downgrade() -> None:
    op.create_table(
        "reaper_game_events",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.String(36), nullable=False),
        sa.Column("turn", sa.Integer, nullable=False),
        sa.Column("phase", sa.String(30), nullable=False),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("data_json", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime, nullable=True),
    )
