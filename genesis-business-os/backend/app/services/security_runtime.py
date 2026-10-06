import os, secrets, time
from collections import defaultdict, deque
from fastapi import HTTPException

_failed=defaultdict(deque)
def login_guard(identity:str):
    now=time.time(); q=_failed[identity]
    while q and q[0] < now-900: q.popleft()
    if len(q)>=8: raise HTTPException(429,'Too many authentication attempts. Try again later.')
def login_failed(identity:str): _failed[identity].append(time.time())
def login_succeeded(identity:str): _failed.pop(identity,None)
def csrf_token(): return secrets.token_urlsafe(32)
def production_guard(env, jwt_secret, database_url, cookie_secure=None, allowed_origins=None, allowed_hosts=None):
    if env=='production':
        if 'development-only' in jwt_secret: raise RuntimeError('Refusing production startup with development JWT secret')
        if database_url.startswith('sqlite:'): raise RuntimeError('Refusing production startup with SQLite; configure PostgreSQL')
        if cookie_secure is False: raise RuntimeError('Refusing production startup without Secure cookies')
        if allowed_origins and ('localhost' in allowed_origins or '*' in allowed_origins): raise RuntimeError('Refusing production startup with unsafe allowed origins')
        if allowed_hosts and ('localhost' in allowed_hosts or '*' in allowed_hosts): raise RuntimeError('Refusing production startup with unsafe allowed hosts')
