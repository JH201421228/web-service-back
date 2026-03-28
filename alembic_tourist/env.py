from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.Tourist.core.config import build_tourist_db_url  # noqa: E402
from app.Tourist.db.base import Base  # noqa: E402
from app.Tourist.models.country_mapping import TouristCountryMapping  # noqa: F401, E402
from app.Tourist.models.country_snapshot import TouristCountrySnapshot  # noqa: F401, E402
from app.Tourist.models.data_source import TouristDataSource  # noqa: F401, E402
from app.Tourist.models.monthly_statistic import TouristMonthlyStatistic  # noqa: F401, E402
from app.Tourist.models.vaccination_reference import TouristVaccinationReference  # noqa: F401, E402

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return build_tourist_db_url()


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table="alembic_version_tourist",
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table="alembic_version_tourist",
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
