import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.main import get_founder_dna, save_founder_dna
from app.models import Tenant, User
from app.schemas import FounderProfileIn


@pytest.fixture
def founder_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    tenant = Tenant(name="DNA test")
    db.add(tenant)
    db.flush()
    user = User(
        tenant_id=tenant.id,
        email="founder@example.com",
        password_hash="test",
    )
    db.add(user)
    db.commit()
    try:
        yield db, user
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_founder_dna_save_records_profile_and_audit(founder_db):
    db, user = founder_db

    saved = save_founder_dna(
        FounderProfileIn(profile={"skills": ["detailing"], "capital": 300}),
        user,
        db,
    )
    loaded = get_founder_dna(user, db)

    assert saved["id"]
    assert saved["version"] == 1
    assert loaded["id"] == saved["id"]
    assert loaded["profile"] == {"skills": ["detailing"], "capital": 300}
    assert loaded["version"] == 1
