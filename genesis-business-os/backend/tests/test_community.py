import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.main import community_block_author, community_feed
from app.models import CommunityPost, Tenant, User


@pytest.fixture
def community_data():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()

    tenant = Tenant(name="Community test")
    db.add(tenant)
    db.flush()
    owner = User(tenant_id=tenant.id, email="owner@example.test", password_hash="test")
    other = User(tenant_id=tenant.id, email="other@example.test", password_hash="test")
    db.add_all([owner, other])
    db.flush()

    owner_post = CommunityPost(
        tenant_id=tenant.id,
        user_id=owner.id,
        display_name="Owner",
        category="ASK",
        body="Owner post",
    )
    other_post = CommunityPost(
        tenant_id=tenant.id,
        user_id=other.id,
        display_name="Other founder",
        category="WIN",
        body="Other post",
    )
    db.add_all([owner_post, other_post])
    db.commit()
    try:
        yield db, owner, other, owner_post, other_post
    finally:
        db.close()
        Base.metadata.drop_all(engine)
        engine.dispose()


def test_community_feed_marks_ownership_and_filters_by_category(community_data):
    db, owner, _, _, _ = community_data

    feed = community_feed(None, owner, db)
    assert {post["body"]: post["is_mine"] for post in feed} == {
        "Owner post": True,
        "Other post": False,
    }

    asks = community_feed("ASK", owner, db)
    assert [post["body"] for post in asks] == ["Owner post"]


def test_blocking_a_post_author_hides_their_posts(community_data):
    db, owner, _, _, other_post = community_data

    result = community_block_author(other_post.id, owner, db)

    assert result == {"ok": True}
    assert [post["body"] for post in community_feed(None, owner, db)] == ["Owner post"]


def test_cannot_block_author_of_own_post(community_data):
    db, owner, _, owner_post, _ = community_data

    with pytest.raises(HTTPException) as error:
        community_block_author(owner_post.id, owner, db)

    assert error.value.status_code == 400
