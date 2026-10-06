import ipaddress, secrets, time
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

def _normalized_host(value):
    if not isinstance(value, str) or not value or value != value.strip():
        return None
    if '://' in value or any(char.isspace() or char in '/?#@*' for char in value):
        return None

    if value.startswith('['):
        closing = value.find(']')
        if closing < 0:
            return None
        hostname = value[1:closing]
        suffix = value[closing + 1:]
        if suffix and (not suffix.startswith(':') or not suffix[1:].isdigit()):
            return None
    elif value.count(':') == 1:
        hostname, port = value.rsplit(':', 1)
        if not port.isdigit():
            return None
    elif ':' in value:
        return None
    else:
        hostname = value

    if not hostname:
        return None
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        if any(char not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-' for char in hostname):
            return None
        return hostname.lower()
    if address.is_loopback or address.is_unspecified:
        return None
    return hostname.lower()

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
    if database.drivername != 'postgresql+psycopg':
        raise RuntimeError('Refusing production startup without PostgreSQL using the configured psycopg driver; SQLite is development-only')
    if not database.host or not database.database or not database.username:
        raise RuntimeError('Refusing production startup with incomplete PostgreSQL connection settings')

    if cookie_secure is not True:
        raise RuntimeError('Refusing production startup without Secure cookies')

    origins = _csv_values(allowed_origins)
    if not origins:
        raise RuntimeError('Refusing production startup without allowed origins')
    for origin in origins:
        if any(char.isspace() for char in origin):
            raise RuntimeError('Refusing production startup with unsafe or missing allowed origins')
        try:
            parsed = urlsplit(origin)
        except ValueError:
            raise RuntimeError('Refusing production startup with unsafe or missing allowed origins') from None
        host = (parsed.hostname or '').lower()
        if (parsed.scheme != 'https' or not host or parsed.path or parsed.query or parsed.fragment
                or parsed.username or parsed.password or '*' in origin
                or host in ('localhost', '127.0.0.1', '::1')):
            raise RuntimeError('Refusing production startup with unsafe or missing allowed origins')

    hosts = _csv_values(allowed_hosts)
    if not hosts:
        raise RuntimeError('Refusing production startup without allowed hosts')
    for host in hosts:
        normalized = _normalized_host(host)
        if not normalized or normalized in ('localhost', 'testserver'):
            raise RuntimeError('Refusing production startup with unsafe or missing allowed hosts')
