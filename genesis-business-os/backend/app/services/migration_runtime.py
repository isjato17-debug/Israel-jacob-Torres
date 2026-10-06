from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory
from sqlalchemy import text
from sqlalchemy.engine import Engine


def assert_current_revision(engine: Engine) -> None:
    backend_root = Path(__file__).resolve().parents[2]
    alembic_config = Config(str(backend_root / 'alembic.ini'))
    expected_heads = ScriptDirectory.from_config(alembic_config).get_heads()
    if len(expected_heads) != 1:
        raise RuntimeError('Genesis requires exactly one Alembic migration head')

    try:
        with engine.connect() as connection:
            current_revisions = list(
                connection.execute(text('SELECT version_num FROM alembic_version')).scalars()
            )
    except Exception as exc:
        raise RuntimeError(
            'Genesis production database is not migrated; run the reviewed Alembic upgrade before startup'
        ) from exc

    if current_revisions != expected_heads:
        raise RuntimeError(
            'Genesis production database revision is not current; run the reviewed Alembic upgrade before startup'
        )
