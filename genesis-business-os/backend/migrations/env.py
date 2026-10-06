from alembic import context
from sqlalchemy import engine_from_config, pool

from app import models  # noqa: F401 - register all mapped tables
from app.config import settings
from app.db import Base
from app.services.security_runtime import production_guard


config = context.config
config.set_main_option('sqlalchemy.url', settings.database_url.replace('%', '%%'))
target_metadata = Base.metadata

if settings.env == 'production':
    production_guard(
        settings.env,
        settings.jwt_secret,
        settings.database_url,
        settings.cookie_secure,
        settings.allowed_origins,
        settings.allowed_hosts,
    )


def run_migrations_offline():
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={'paramstyle': 'named'},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()
    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
