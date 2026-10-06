import pytest
from app.services.security_runtime import production_guard

def test_prod_rejects_dev_secret():
    with pytest.raises(RuntimeError): production_guard('production','development-only-change-me-32-bytes-minimum','postgresql://x')
def test_prod_rejects_sqlite():
    with pytest.raises(RuntimeError): production_guard('production','x'*64,'sqlite:///x.db')
def test_prod_accepts_secure_baseline():
    secure = {
        'cookie_secure': True,
        'allowed_origins': 'https://genesis.example',
        'allowed_hosts': 'genesis.example',
    }
    production_guard('production','x'*64,'postgresql+psycopg://genesis@db.example/genesis',**secure)
    invalid_configs = [
        {'database_url': 'postgresql://'},
        {'cookie_secure': False},
        {'allowed_origins': ''},
        {'allowed_origins': 'http://genesis.example'},
        {'allowed_origins': 'https://localhost'},
        {'allowed_hosts': ''},
        {'allowed_hosts': '*'},
        {'allowed_hosts': 'localhost'},
    ]
    for invalid in invalid_configs:
        values = {
            'jwt_secret': 'x'*64,
            'database_url': 'postgresql+psycopg://genesis@db.example/genesis',
            **secure,
            **invalid,
        }
        with pytest.raises(RuntimeError):
            production_guard('production',values.pop('jwt_secret'),values.pop('database_url'),**values)
