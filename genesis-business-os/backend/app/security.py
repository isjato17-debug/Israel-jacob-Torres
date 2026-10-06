from datetime import datetime, timedelta, timezone
import hashlib, secrets
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Request
from sqlalchemy.orm import Session
from .config import settings
from .db import get_db
from .models import User, Tenant, SessionRecord

pwd=CryptContext(schemes=['argon2'], deprecated='auto'); ALG='HS256'; COOKIE='genesis_session'; CSRF_COOKIE='genesis_csrf'
def hash_password(p): return pwd.hash(p)
def verify_password(p,h): return pwd.verify(p,h)
def token_hash(v): return hashlib.sha256(v.encode()).hexdigest()
def create_session(db:Session,user:User,request:Request):
    now=datetime.now(timezone.utc); sid=secrets.token_urlsafe(32); csrf=secrets.token_urlsafe(32)
    rec=SessionRecord(id=token_hash(sid),tenant_id=user.tenant_id,user_id=user.id,csrf_hash=token_hash(csrf),created_at=now,last_seen_at=now,expires_at=now+timedelta(hours=settings.session_absolute_hours),ip_hash=token_hash(request.client.host if request.client else 'unknown'))
    db.add(rec); return sid,csrf

def set_session_cookies(response,sid,csrf):
    response.set_cookie(COOKIE,sid,httponly=True,secure=settings.cookie_secure,samesite='strict',max_age=settings.session_absolute_hours*3600,path='/')
    response.set_cookie(CSRF_COOKIE,csrf,httponly=False,secure=settings.cookie_secure,samesite='strict',max_age=settings.session_absolute_hours*3600,path='/')
def clear_session_cookies(response):
    response.delete_cookie(COOKIE,path='/'); response.delete_cookie(CSRF_COOKIE,path='/')
def current_session(request:Request,db:Session=Depends(get_db)):
    raw=request.cookies.get(COOKIE)
    if not raw: raise HTTPException(401,'Authentication required')
    rec=db.get(SessionRecord,token_hash(raw)); now=datetime.now(timezone.utc)
    if not rec or rec.revoked_at: raise HTTPException(401,'Invalid or expired session')
    expires_at=rec.expires_at
    if expires_at.tzinfo is None: expires_at=expires_at.replace(tzinfo=timezone.utc)
    if expires_at<now: raise HTTPException(401,'Invalid or expired session')
    last=rec.last_seen_at
    if last.tzinfo is None: last=last.replace(tzinfo=timezone.utc)
    if now-last>timedelta(minutes=settings.session_idle_minutes): raise HTTPException(401,'Session timed out')
    rec.last_seen_at=now; db.commit(); return rec
def current_user(rec:SessionRecord=Depends(current_session),db:Session=Depends(get_db)):
    u=db.get(User,rec.user_id)
    if not u or not u.active or u.tenant_id!=rec.tenant_id: raise HTTPException(401,'Invalid session')
    return u
def require_csrf(request:Request,rec:SessionRecord=Depends(current_session)):
    supplied=request.headers.get('X-CSRF-Token',''); cookie=request.cookies.get(CSRF_COOKIE,'')
    if not supplied or not cookie or not secrets.compare_digest(supplied,cookie) or not secrets.compare_digest(token_hash(supplied),rec.csrf_hash): raise HTTPException(403,'CSRF validation failed')
    return True
def require_owner(user:User=Depends(current_user)):
    if user.role not in {'owner','admin'}: raise HTTPException(403,'Owner/admin required')
    return user
def ensure_tenant(obj,user):
    if not obj or getattr(obj,'tenant_id',None)!=user.tenant_id: raise HTTPException(404,'Resource not found')
    return obj
def ensure_not_lockdown(db:Session,user:User):
    t=db.get(Tenant,user.tenant_id)
    if settings.lockdown or (t and t.lockdown): raise HTTPException(423,'Lockdown mode: write/action operations disabled')
