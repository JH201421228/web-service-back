"""add_tourist_reference_tables

Revision ID: 20260329_0003
Revises: 20260329_0002
Create Date: 2026-03-29 12:30:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260329_0003"
down_revision: Union[str, Sequence[str], None] = "20260329_0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tourist_country_mappings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("app_country_code", sa.String(length=3), nullable=False),
        sa.Column("iso_alpha2", sa.String(length=2), nullable=False),
        sa.Column("iso_alpha3", sa.String(length=3), nullable=True),
        sa.Column("country_name", sa.String(length=100), nullable=False),
        sa.Column("country_name_en", sa.String(length=200), nullable=True),
        sa.Column("aliases_json", sa.Text(), nullable=False),
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tourist_country_mappings_app_country_code"),
        "tourist_country_mappings",
        ["app_country_code"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tourist_country_mappings_country_name"),
        "tourist_country_mappings",
        ["country_name"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tourist_country_mappings_iso_alpha2"),
        "tourist_country_mappings",
        ["iso_alpha2"],
        unique=True,
    )
    op.create_index(
        op.f("ix_tourist_country_mappings_iso_alpha3"),
        "tourist_country_mappings",
        ["iso_alpha3"],
        unique=False,
    )

    op.create_table(
        "tourist_vaccination_references",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("vaccine_code", sa.String(length=20), nullable=False),
        sa.Column("vaccine_name", sa.String(length=255), nullable=False),
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_tourist_vaccination_references_vaccine_code"),
        "tourist_vaccination_references",
        ["vaccine_code"],
        unique=True,
    )

    op.create_table(
        "tourist_monthly_statistics",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("metric_key", sa.String(length=50), nullable=False),
        sa.Column("base_ym", sa.String(length=6), nullable=False),
        sa.Column("segment_key", sa.String(length=50), nullable=False),
        sa.Column("segment_label", sa.String(length=100), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("previous_quantity", sa.Integer(), nullable=True),
        sa.Column("change_rate", sa.Float(), nullable=True),
        sa.Column("source_key", sa.String(length=50), nullable=False),
        sa.Column("synced_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "metric_key",
            "base_ym",
            "segment_key",
            name="uq_tourist_monthly_statistics_metric_segment",
        ),
    )
    op.create_index(
        op.f("ix_tourist_monthly_statistics_base_ym"),
        "tourist_monthly_statistics",
        ["base_ym"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tourist_monthly_statistics_metric_key"),
        "tourist_monthly_statistics",
        ["metric_key"],
        unique=False,
    )
    op.create_index(
        op.f("ix_tourist_monthly_statistics_segment_key"),
        "tourist_monthly_statistics",
        ["segment_key"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_tourist_monthly_statistics_segment_key"), table_name="tourist_monthly_statistics")
    op.drop_index(op.f("ix_tourist_monthly_statistics_metric_key"), table_name="tourist_monthly_statistics")
    op.drop_index(op.f("ix_tourist_monthly_statistics_base_ym"), table_name="tourist_monthly_statistics")
    op.drop_table("tourist_monthly_statistics")
    op.drop_index(
        op.f("ix_tourist_vaccination_references_vaccine_code"),
        table_name="tourist_vaccination_references",
    )
    op.drop_table("tourist_vaccination_references")
    op.drop_index(op.f("ix_tourist_country_mappings_iso_alpha3"), table_name="tourist_country_mappings")
    op.drop_index(op.f("ix_tourist_country_mappings_iso_alpha2"), table_name="tourist_country_mappings")
    op.drop_index(op.f("ix_tourist_country_mappings_country_name"), table_name="tourist_country_mappings")
    op.drop_index(
        op.f("ix_tourist_country_mappings_app_country_code"),
        table_name="tourist_country_mappings",
    )
    op.drop_table("tourist_country_mappings")
