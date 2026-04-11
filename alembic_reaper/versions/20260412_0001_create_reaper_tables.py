"""create reaper tables

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12
"""
from alembic import op
import sqlalchemy as sa

revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reaper_rooms",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("host_uid", sa.String(128), nullable=False),
        sa.Column("status", sa.String(20), default="waiting"),
        sa.Column("max_players", sa.Integer, default=6),
        sa.Column("bot_count", sa.Integer, default=5),
        sa.Column("created_at", sa.DateTime, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("ended_at", sa.DateTime, nullable=True),
        sa.Column("winner", sa.String(20), nullable=True),
    )

    op.create_table(
        "reaper_players",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.String(36), sa.ForeignKey("reaper_rooms.id"), nullable=False),
        sa.Column("uid", sa.String(128), nullable=False),
        sa.Column("nickname", sa.String(50), nullable=False),
        sa.Column("hashtag", sa.String(10), nullable=False),
        sa.Column("is_bot", sa.Boolean, default=False),
        sa.Column("seat_number", sa.Integer, nullable=False),
        sa.Column("role", sa.String(20), nullable=True),
        sa.Column("is_alive", sa.Boolean, default=True),
        sa.Column("joined_at", sa.DateTime, nullable=True),
        sa.Column("grim_score", sa.Integer, default=50),
        sa.Column("power_score", sa.Integer, default=20),
        sa.Column("influence_score", sa.Integer, default=30),
        sa.Column("threat_score", sa.Integer, default=20),
    )

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


def downgrade() -> None:
    op.drop_table("reaper_game_events")
    op.drop_table("reaper_players")
    op.drop_table("reaper_rooms")
