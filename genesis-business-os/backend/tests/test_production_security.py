import pytest
from app.services.security_runtime import production_guard

def test_prod_rejects_dev_secret():
    with pytest.raises(RuntimeError): production_guard('production','development-only-change-me-32-bytes-minimum','postgresql://x')
def test_prod_rejects_sqlite():
    with pytest.raises(RuntimeError): production_guard('production','x'*64,'sqlite:///x.db')
def test_prod_accepts_secure_baseline():
    production_guard('production','x'*64,'postgresql://db')
