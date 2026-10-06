import secrets, time
from collections import defaultdict, deque
from urllib.parse import urlsplit

from fastapi import HTTPException
from sqlalchemy.exc import ArgumentError
from sqlalchemy.engine import make_url

_failed=defaultdict(deque)
def login_guard(identity:str):
    now=time.time(); q=_failed[identity]
    while q and q[0] < now-900: q.popleft()
    if len(q)>=8: raise HTTPException(429,'Too many authentication attempts. Try again later.')
def login_failed(identity:str): _failed[identity].append(time.time())
def login_succeeded(identity:str): _failed.pop(identity,None)
def csrf_token(): return secrets.token_urlsafe(32)

def _csv_values(value):
    if isinstance(value, str):
        return [item.strip() for item in value.split(',') if item.strip()]
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    return []

def production_guard(env, jwt_secret, database_url, cookie_secure=None, allowed_origins=None, allowed_hosts=None):
    if env != 'production':
        return

    if not isinstance(jwt_secret, str) or len(jwt_secret) < 32 or 'development-only' in jwt_secret:
        raise RuntimeError('Refusing production startup without a strong production JWT secret')

    if not isinstance(database_url, str) or not database_url.strip():
        raise RuntimeError('Refusing production startup without a PostgreSQL database URL')
    try:
        database = make_url(database_url)
    except (ArgumentError, TypeError, ValueError):
        raise RuntimeError('Refusing production startup with an invalid database URL') from None
    if database.drivername not in ('postgresql', 'postgresql+psycopg'):
        raise RuntimeError('Refusing production startup without PostgreSQL; SQLite is development-only')
    if not database.host or not database.database or not database.username:
        raise RuntimeError('Refusing production startup with incomplete PostgreSQL connection settings')

    if cookie_secure is not True:
        raise RuntimeError('Refusing production startup without Secure cookies')

    origins = _csv_values(allowed_origins)
    if not origins:
        raise RuntimeError('Refusing production startup without allowed origins')
    for origin in origins:
        parsed = urlsplit(origin)
        host = (parsed.hostname or '').lower()
        if parsed.scheme != 'https' or not host or '*' in origin or host in ('localhost', '127.0.0.1', '::1'):
            raise RuntimeError('Refusing production startup with unsafe or missing allowed origins')

    hosts = _csv_values(allowed_hosts)
    if not hosts:
        raise RuntimeError('Refusing production startup without allowed hosts')
    for host in hosts:
        normalized = host.lower().split(':', 1)[0].strip('[]')
        if '*' in host or normalized in ('localhost', '127.0.0.1', '::1', 'testserver'):
            raise RuntimeError('Refusing production startup with unsafe or missing allowed hosts')
