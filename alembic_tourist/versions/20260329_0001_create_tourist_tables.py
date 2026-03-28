"""create_tourist_tables

Revision ID: 20260329_0001
Revises:
Create Date: 2026-03-29 02:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tourist_country_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("country_code", sa.String(length=2), nullable=False),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.Column("country_name_en", sa.String(length=200), nullable=True),
        sa.Column("continent", sa.String(length=60), nullable=True),
        sa.Column("flag_image_url", sa.String(length=1000), nullable=True),
        sa.Column("map_image_url", sa.String(length=1000), nullable=True),
        sa.Column("alert_level", sa.String(length=20), nullable=False),
        sa.Column("alert_summary", sa.String(length=500), nullable=True),
        sa.Column("attention", sa.String(length=50), nullable=True),
        sa.Column("attention_partial", sa.String(length=50), nullable=True),
        sa.Column("attention_note", sa.Text(), nullable=True),
        sa.Column("control", sa.String(length=50), nullable=True),
        sa.Column("control_partial", sa.String(length=50), nullable=True),
        sa.Column("control_note", sa.Text(), nullable=True),
        sa.Column("limita", sa.String(length=50), nullable=True),
        sa.Column("limita_partial", sa.String(length=50), nullable=True),
        sa.Column("limita_note", sa.Text(), nullable=True),
        sa.Column("ban", sa.String(length=50), nullable=True),
        sa.Column("ban_partial", sa.String(length=50), nullable=True),
        sa.Column("ban_note", sa.Text(), nullable=True),
        sa.Column("entry_requirement", sa.Text(), nullable=True),
        sa.Column("entry_requirement_details", sa.Text(), nullable=True),
        sa.Column("quarantine_summary", sa.String(length=500), nullable=True),
        sa.Column("quarantine_diseases", sa.Text(), nullable=True),
        sa.Column("source_updated_at", sa.String(length=50), nullable=True),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tourist_country_snapshots_alert_level"),
        "tourist_country_snapshots",
        ["alert_level"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tourist_country_snapshots_country_code"),
        "tourist_country_snapshots",
        ["country_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tourist_country_snapshots_country_name"),
        "tourist_country_snapshots",
        ["country_name"],
        unique=False,
    )

    op.create_table(
        "tourist_data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("display_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("label", sa.String(length=200), nullable=False),
        sa.Column("organization", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=1000), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=20), server_default="pending", nullable=False),
        sa.Column("item_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tourist_data_sources_source_key"),
        "tourist_data_sources",
        ["source_key"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tourist_data_sources_source_key"), table_name="tourist_data_sources")
    op.drop_table("tourist_data_sources")
    op.drop_index(op.f("ix_tourist_country_snapshots_country_name"), table_name="tourist_country_snapshots")
    op.drop_index(op.f("ix_tourist_country_snapshots_country_code"), table_name="tourist_country_snapshots")
    op.drop_index(op.f("ix_tourist_country_snapshots_alert_level"), table_name="tourist_country_snapshots")
    op.drop_table("tourist_country_snapshots")
