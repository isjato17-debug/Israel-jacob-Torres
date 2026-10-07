"""Local control regressions; these do not prove deployment edge configuration."""
from datetime import datetime, timedelta, timezone
import time
from fastapi.testclient import TestClient
from app.main import app, buckets
from app.config import settings
from app.db import SessionLocal
from app.models import SessionRecord, User
from app.security import token_hash


def signed_in(label):
    client = TestClient(app)
    response = client.post('/api/auth/register', json={
        'tenant_name': label, 'email': f'{label}@example.com',
        'password': 'VeryStrongPassword!123',
    })
    assert response.status_code == 200, response.text
    return client, response, {'X-CSRF-Token': response.json()['csrf']}


def test_csrf_cookies_headers_hosts_and_cors(monkeypatch):
    monkeypatch.setattr(settings, 'cookie_secure', True)
    client, response, headers = signed_in('controls-cookies')
    cookies = response.headers.get_list('set-cookie')
    assert all('Secure' in value and 'SameSite=strict' in value for value in cookies)
    assert 'HttpOnly' in next(value for value in cookies if value.startswith('genesis_session='))
    monkeypatch.setattr(settings, 'cookie_secure', False)
    # HTTPS cookies are deliberately not sent over HTTP; use HTTPS for this session.
    client.base_url = 'https://testserver'
    for supplied in ({}, {'X-CSRF-Token': 'wrong'}):
        assert client.post('/api/businesses', headers=supplied, json={'name':'blocked','twin':{}}).status_code == 403
    assert client.post('/api/businesses', headers=headers, json={'name':'allowed','twin':{}}).status_code == 200
    health = client.get('/healthz')
    assert "frame-ancestors 'none'" in health.headers['content-security-policy']
    assert health.headers['x-content-type-options'] == 'nosniff'
    assert health.headers['cache-control'] == 'no-store'
    assert client.get('/healthz', headers={'Host':'untrusted.example'}).status_code == 400
    good = client.options('/api/me', headers={'Origin':'http://localhost:8000','Access-Control-Request-Method':'GET'})
    bad = client.options('/api/me', headers={'Origin':'https://untrusted.example','Access-Control-Request-Method':'GET'})
    assert good.status_code == 200 and good.headers['access-control-allow-origin'] == 'http://localhost:8000'
    assert bad.status_code == 400 and 'access-control-allow-origin' not in bad.headers
    monkeypatch.setattr(settings, 'env', 'production')
    assert client.get('/healthz').headers['strict-transport-security'] == 'max-age=31536000; includeSubDomains'


def test_logout_revokes_session_and_expiry():
    client, _, headers = signed_in('controls-logout')
    raw = client.cookies.get('genesis_session')
    assert client.post('/api/auth/logout', headers=headers).status_code == 200
    client.cookies.set('genesis_session', raw)
    assert client.get('/api/me').status_code == 401
    client, _, _ = signed_in('controls-expiry')
    with SessionLocal() as db:
        record = db.get(SessionRecord, token_hash(client.cookies.get('genesis_session')))
        record.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        db.commit()
    assert client.get('/api/me').status_code == 401


def test_idle_timeout_and_role_authorization():
    client, response, headers = signed_in('controls-idle')
    with SessionLocal() as db:
        record = db.get(SessionRecord, token_hash(client.cookies.get('genesis_session')))
        record.last_seen_at = datetime.now(timezone.utc) - timedelta(minutes=settings.session_idle_minutes+1)
        db.commit()
    assert client.get('/api/me').status_code == 401
    client, response, headers = signed_in('controls-role')
    with SessionLocal() as db:
        db.get(User, response.json()['user']['id']).role = 'member'
        db.commit()
    assert client.post('/api/security/lockdown', headers=headers, json={'enabled':True}).status_code == 403


def test_request_rate_limit_returns_429():
    key = 'testclient'
    old = buckets.pop(key, None)
    try:
        buckets[key].extend([time.time()] * 120)
        response = TestClient(app, raise_server_exceptions=False).get('/healthz')
        assert response.status_code == 429
        assert response.headers['retry-after'] == '60'
    finally:
        buckets.pop(key, None)
        if old is not None:
            buckets[key] = old
