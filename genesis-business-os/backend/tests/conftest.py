import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))

_TEST_DIRECTORY = Path(tempfile.mkdtemp(prefix='genesis-backend-tests-'))
_TEST_DATABASE = _TEST_DIRECTORY / 'backend-tests.sqlite'

# API tests perform writes, so never let them inherit a developer or production
# database URL from the invoking shell.
os.environ['GENESIS_ENV'] = 'development'
os.environ['GENESIS_DATABASE_URL'] = f'sqlite:///{_TEST_DATABASE.as_posix()}'
os.environ.setdefault('GENESIS_JWT_SECRET', 'isolated-backend-test-secret-' + ('x' * 40))


def pytest_unconfigure(config):
    database_module = sys.modules.get('app.db')
    if database_module is not None:
        database_module.engine.dispose()
    shutil.rmtree(_TEST_DIRECTORY, ignore_errors=True)
