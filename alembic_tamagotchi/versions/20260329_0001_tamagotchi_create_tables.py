"""create_tamagotchi_tables

Revision ID: 20260329_0001_tamagotchi
Revises:
Create Date: 2026-03-29 21:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0001_tamagotchi"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tamagotchi_players",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("install_id", sa.String(length=128), nullable=False),
        sa.Column("language", sa.String(length=5), nullable=False),
        sa.Column("nickname", sa.String(length=60), nullable=False),
        sa.Column("pet_name", sa.String(length=60), nullable=False),
        sa.Column("starter_id", sa.String(length=20), nullable=False),
        sa.Column("exp", sa.Integer(), nullable=False),
        sa.Column("coins", sa.Integer(), nullable=False),
        sa.Column("mood", sa.Integer(), nullable=False),
        sa.Column("energy", sa.Integer(), nullable=False),
        sa.Column("cleanliness", sa.Integer(), nullable=False),
        sa.Column("bond", sa.Integer(), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.Column("last_sync_date", sa.Date(), nullable=True),
        sa.Column("last_health_source", sa.String(length=20), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tamagotchi_players_install_id"),
        "tamagotchi_players",
        ["install_id"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tamagotchi_players_last_sync_date"),
        "tamagotchi_players",
        ["last_sync_date"],
        unique=False,
    )

    op.create_table(
        "tamagotchi_daily_histories",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("date_key", sa.Date(), nullable=False),
        sa.Column("steps", sa.Integer(), nullable=False),
        sa.Column("sleep_hours", sa.Float(), nullable=False),
        sa.Column("avg_heart_rate", sa.Integer(), nullable=False),
        sa.Column("calories", sa.Integer(), nullable=False),
        sa.Column("active_minutes", sa.Integer(), nullable=False),
        sa.Column("health_source", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("exp_gained", sa.Integer(), nullable=False),
        sa.Column("coins_gained", sa.Integer(), nullable=False),
        sa.Column("total_exp", sa.Integer(), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["tamagotchi_players.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "player_id",
            "date_key",
            name="uq_tamagotchi_daily_histories_player_date",
        ),
    )
    op.create_index(
        op.f("ix_tamagotchi_daily_histories_player_id"),
        "tamagotchi_daily_histories",
        ["player_id"],
        unique=False,
    )
    op.create_index(
        "ix_tamagotchi_daily_histories_date_key",
        "tamagotchi_daily_histories",
        ["date_key"],
        unique=False,
    )
    op.create_index(
        "ix_tamagotchi_daily_histories_player_date",
        "tamagotchi_daily_histories",
        ["player_id", "date_key"],
        unique=False,
    )

    op.create_table(
        "tamagotchi_daily_leaderboards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date_key", sa.Date(), nullable=False),
        sa.Column("install_id", sa.String(length=128), nullable=False),
        sa.Column("nickname", sa.String(length=60), nullable=False),
        sa.Column("pet_name", sa.String(length=60), nullable=False),
        sa.Column("starter_id", sa.String(length=20), nullable=False),
        sa.Column("score", sa.Integer(), nullable=False),
        sa.Column("streak", sa.Integer(), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False),
        sa.Column("total_exp", sa.Integer(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "date_key",
            "install_id",
            name="uq_tamagotchi_daily_leaderboards_date_install",
        ),
    )
    op.create_index(
        op.f("ix_tamagotchi_daily_leaderboards_date_key"),
        "tamagotchi_daily_leaderboards",
        ["date_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tamagotchi_daily_leaderboards_install_id"),
        "tamagotchi_daily_leaderboards",
        ["install_id"],
        unique=False,
    )
    op.create_index(
        "ix_tamagotchi_daily_leaderboards_rank",
        "tamagotchi_daily_leaderboards",
        ["date_key", "score", "submitted_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_tamagotchi_daily_leaderboards_rank",
        table_name="tamagotchi_daily_leaderboards",
    )
    op.drop_index(
        op.f("ix_tamagotchi_daily_leaderboards_install_id"),
        table_name="tamagotchi_daily_leaderboards",
    )
    op.drop_index(
        op.f("ix_tamagotchi_daily_leaderboards_date_key"),
        table_name="tamagotchi_daily_leaderboards",
    )
    op.drop_table("tamagotchi_daily_leaderboards")
    op.drop_index(
        "ix_tamagotchi_daily_histories_player_date",
        table_name="tamagotchi_daily_histories",
    )
    op.drop_index(
        "ix_tamagotchi_daily_histories_date_key",
        table_name="tamagotchi_daily_histories",
    )
    op.drop_index(
        op.f("ix_tamagotchi_daily_histories_player_id"),
        table_name="tamagotchi_daily_histories",
    )
    op.drop_table("tamagotchi_daily_histories")
    op.drop_index(
        op.f("ix_tamagotchi_players_last_sync_date"),
        table_name="tamagotchi_players",
    )
    op.drop_index(
        op.f("ix_tamagotchi_players_install_id"),
        table_name="tamagotchi_players",
    )
    op.drop_table("tamagotchi_players")
