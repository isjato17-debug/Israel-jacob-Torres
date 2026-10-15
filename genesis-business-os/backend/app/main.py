import json, secrets, time, hashlib, hmac, os
from datetime import datetime, timezone
from collections import defaultdict, deque
from pathlib import Path
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import select
from .db import Base, engine, get_db
from .models import *
from .schemas import *
from .security import *
from .config import settings
from .services.product_engine import founder_score, battle_mode, failure_lab, execution_plan, variance_report
from .services.consultant import generate_candidates, executive_board, financial_model, decision_hash
from .services.security_runtime import production_guard, login_guard, login_failed, login_succeeded
from .services.migration_runtime import assert_current_revision
from .services.execution_hub import CATALOG, public_catalog, connection_status, prepare as prepare_execution, execute as execute_provider
from .v2.router import router as v2_router
from .v2.journey import router as journey_router
from .v2.growth import router as growth_router
from .v2.consultation import router as consultation_router
from .services.readiness import check_readiness
from .v2.partners import router as partners_router
from .v2.partner_promotions import router as partner_promotions_router

production_guard(settings.env, settings.jwt_secret, settings.database_url, settings.cookie_secure, settings.allowed_origins, settings.allowed_hosts)
if settings.env == 'production':
    assert_current_revision(engine)
else:
    Base.metadata.create_all(engine)
app=FastAPI(title='Genesis Business OS',version='0.1.0',docs_url='/docs' if settings.env!='production' else None,redoc_url=None)
app.include_router(v2_router)
app.include_router(journey_router)
app.include_router(growth_router)
app.include_router(consultation_router)
app.include_router(partners_router)
app.include_router(partner_promotions_router)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=[x.strip() for x in settings.allowed_hosts.split(',') if x.strip()])
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.allowed_origins.split(',')],allow_credentials=True,allow_methods=['GET','POST','PUT','PATCH','DELETE'],allow_headers=['Content-Type','X-Request-ID','X-CSRF-Token'])
PRODUCT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_ROOT = PRODUCT_ROOT / 'frontend'
app.mount('/static', StaticFiles(directory=FRONTEND_ROOT / 'public' / 'static'), name='static')

buckets=defaultdict(deque)
@app.middleware('http')
async def harden(request:Request, call_next):
    ip=request.client.host if request.client else 'unknown'; now=time.time(); q=buckets[ip]
    while q and q[0]<now-60:q.popleft()
    if len(q)>=120:
        return JSONResponse({'detail':'Rate limit exceeded'},status_code=429,headers={'Retry-After':'60','Cache-Control':'no-store'})
    q.append(now)
    response=await call_next(request)
    response.headers['X-Content-Type-Options']='nosniff'; response.headers['X-Frame-Options']='DENY'
    response.headers['Referrer-Policy']='no-referrer'; response.headers['Cache-Control']='no-store'; response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']="default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'; object-src 'none'"
    if settings.env=='production': response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return response

def audit(db,user,action,rtype,rid,details=None):
    db.add(AuditEvent(tenant_id=user.tenant_id,actor_id=user.id,action=action,resource_type=rtype,resource_id=rid,details_json=json.dumps(details or {})))

def business_for(db,bid,user): return ensure_tenant(db.get(Business,bid),user)

@app.get('/')
def home(): return FileResponse(FRONTEND_ROOT / 'index.html')
@app.get('/healthz')
def health(): return {'status':'ok','lockdown':settings.lockdown}

@app.get('/api/readyz')
def readiness():
    checks = check_readiness(engine, settings.env)
    ready = all(checks.values())
    return JSONResponse({"status": "ready" if ready else "not_ready", "checks": checks},
                        status_code=200 if ready else 503)

@app.post('/api/auth/register',dependencies=[Depends(require_csrf)] if False else [])
def register(x:Register, request:Request, db:Session=Depends(get_db)):
    if db.scalar(select(User).where(User.email==x.email.lower())): raise HTTPException(409,'Email already registered')
    t=Tenant(name=x.tenant_name); db.add(t); db.flush(); u=User(tenant_id=t.id,email=x.email.lower(),password_hash=hash_password(x.password),role='owner'); db.add(u); db.flush(); sid,csrf=create_session(db,u,request); audit(db,u,'register','tenant',t.id); db.commit(); response=JSONResponse({'user':{'id':u.id,'tenant_id':u.tenant_id,'email':u.email,'role':u.role},'csrf':csrf}); set_session_cookies(response,sid,csrf); return response
@app.post('/api/auth/login')
def login(x:Login, request:Request, db:Session=Depends(get_db)):
    identity=(request.client.host if request.client else 'unknown')+'|'+x.email.lower(); login_guard(identity); u=db.scalar(select(User).where(User.email==x.email.lower()))
    if not u or not verify_password(x.password,u.password_hash): login_failed(identity); raise HTTPException(401,'Invalid email or password')
    login_succeeded(identity); sid,csrf=create_session(db,u,request); audit(db,u,'login','user',u.id); db.commit(); response=JSONResponse({'user':{'id':u.id,'tenant_id':u.tenant_id,'email':u.email,'role':u.role},'csrf':csrf}); set_session_cookies(response,sid,csrf); return response
@app.post('/api/auth/logout')
def logout(request:Request, rec:SessionRecord=Depends(current_session), _:bool=Depends(require_csrf), db:Session=Depends(get_db)):
    rec.revoked_at=datetime.now(timezone.utc); db.commit(); response=JSONResponse({'ok':True}); clear_session_cookies(response); return response
@app.get('/api/me')
def me(u:User=Depends(current_user)): return {'id':u.id,'tenant_id':u.tenant_id,'email':u.email,'role':u.role}

@app.post('/api/founder')
def founder(x:FounderIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); f=FounderProfile(tenant_id=u.tenant_id,owner_id=u.id,objective=x.objective,constraints_json=json.dumps(x.constraints)); db.add(f); db.flush(); audit(db,u,'create','founder_profile',f.id); db.commit(); return {'id':f.id,'objective':f.objective,'constraints':x.constraints}
@app.get('/api/founder')
def founder_list(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(FounderProfile).where(FounderProfile.tenant_id==u.tenant_id)).all(); return [{'id':r.id,'objective':r.objective,'constraints':json.loads(r.constraints_json)} for r in rows]

@app.post('/api/businesses')
def create_business(x:BusinessIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); b=Business(tenant_id=u.tenant_id,name=x.name,twin_json=json.dumps(x.twin)); db.add(b); db.flush(); audit(db,u,'create','business',b.id); db.commit(); return {'id':b.id,'name':b.name,'state':b.lifecycle_state,'twin':x.twin}
@app.get('/api/businesses')
def list_businesses(u:User=Depends(current_user),db:Session=Depends(get_db)):
    rows=db.scalars(select(Business).where(Business.tenant_id==u.tenant_id)).all(); return [{'id':r.id,'name':r.name,'state':r.lifecycle_state,'twin_version':r.twin_version,'twin':json.loads(r.twin_json)} for r in rows]

@app.post('/api/evidence')
def add_evidence(x:EvidenceIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); business_for(db,x.business_id,u); allowed={'verified','user_assertion','derived','ai_assumption','forecast','actual'}
    if x.classification not in allowed: raise HTTPException(422,'Invalid evidence classification')
    e=Evidence(tenant_id=u.tenant_id,business_id=x.business_id,classification=x.classification,value=x.value,source_ref=x.source_ref,confidence=x.confidence); db.add(e); db.flush(); audit(db,u,'create','evidence',e.id,{'classification':x.classification}); db.commit(); return {'id':e.id,'classification':e.classification}

@app.post('/api/decisions')
def create_decision(x:DecisionIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); b=business_for(db,x.business_id,u)
    rec={'agents':{'CEO':'Evaluate strategic fit','CFO':'Validate cash/runway constraints','CMO':'Validate demand/acquisition','COO':'Validate capacity','Risk':'Stress downside','Cyber':'Check data/action permissions'},'required_approval':x.risk_tier>=3,'twin_version':b.twin_version}
    d=Decision(tenant_id=u.tenant_id,business_id=b.id,question=x.question,risk_tier=x.risk_tier,recommendation_json=json.dumps(rec)); db.add(d); db.flush(); audit(db,u,'create','decision',d.id,{'risk_tier':x.risk_tier}); db.commit(); return {'id':d.id,'status':d.status,'risk_tier':d.risk_tier,'board':rec}
@app.post('/api/decisions/{did}/approve')
def approve(did:str,x:ApproveIn,u:User=Depends(require_owner),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); d=ensure_tenant(db.get(Decision,did),u)
    if not x.confirm: raise HTTPException(400,'Explicit confirmation required')
    d.status='approved'; d.approved_by=u.id; capability=secrets.token_urlsafe(24) if d.risk_tier<=3 else None
    audit(db,u,'approve','decision',d.id,{'capability_issued':bool(capability),'tier':d.risk_tier}); db.commit()
    return {'id':d.id,'status':d.status,'capability':capability,'note':'Tier 4 remains non-autonomous' if d.risk_tier==4 else 'Capability is illustrative and one-response only in this MVP'}

@app.post('/api/security/lockdown')
def lockdown(x:LockdownIn,u:User=Depends(require_owner),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    t=db.get(Tenant,u.tenant_id); t.lockdown=x.enabled; audit(db,u,'lockdown_on' if x.enabled else 'lockdown_off','tenant',t.id); db.commit(); return {'lockdown':t.lockdown}
@app.get('/api/security/audit')
def audit_log(u:User=Depends(require_owner),db:Session=Depends(get_db)):
    rows=db.scalars(select(AuditEvent).where(AuditEvent.tenant_id==u.tenant_id).order_by(AuditEvent.created_at.desc()).limit(100)).all()
    return [{'time':r.created_at,'action':r.action,'resource_type':r.resource_type,'resource_id':r.resource_id} for r in rows]

@app.post('/api/consultant/generate')
def consultant_generate(x:GenerateBusinessIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); c=generate_candidates(x.objective,x.constraints); audit(db,u,'generate','business_candidates','new',{'count':len(c)}); db.commit(); return {'objective':x.objective,'candidates':c,'notice':'Planning values remain assumptions until verified.'}
@app.patch('/api/businesses/{bid}/twin')
def patch_twin(bid:str,x:TwinPatchIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); b=business_for(db,bid,u); twin=json.loads(b.twin_json or '{}'); twin.update(x.patch); b.twin_json=json.dumps(twin); b.twin_version+=1; audit(db,u,'update','business_twin',b.id,{'version':b.twin_version}); db.commit(); return {'id':b.id,'twin_version':b.twin_version,'twin':twin,'financials':financial_model(twin)}
@app.post('/api/businesses/{bid}/actuals')
def add_actual(bid:str,x:ActualIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); b=business_for(db,bid,u); a=ActualObservation(tenant_id=u.tenant_id,business_id=bid,key=x.key,value=str(x.value)); db.add(a); twin=json.loads(b.twin_json or '{}'); forecast=twin.get(x.key); twin[x.key]=x.value; b.twin_json=json.dumps(twin); b.twin_version+=1
    variance=None
    try: variance=round(x.value-float(forecast),2) if forecast is not None else None
    except (TypeError, ValueError): variance=None
    audit(db,u,'actual','business_twin',b.id,{'key':x.key,'forecast':forecast,'actual':x.value,'variance':variance}); db.commit(); return {'key':x.key,'forecast':forecast,'actual':x.value,'variance':variance,'twin_version':b.twin_version}
@app.post('/api/businesses/{bid}/board')
def run_board(bid:str,x:BoardRunIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); b=business_for(db,bid,u); ev=db.scalars(select(Evidence).where(Evidence.tenant_id==u.tenant_id,Evidence.business_id==bid)).all(); evidence=[{'classification':e.classification,'value':e.value,'source_ref':e.source_ref,'confidence':e.confidence} for e in ev]; twin=json.loads(b.twin_json or '{}'); result=executive_board(x.question,twin,evidence); risk=3 if result['conflicts'] else 2; d=Decision(tenant_id=u.tenant_id,business_id=bid,question=x.question,risk_tier=risk,recommendation_json=json.dumps(result)); db.add(d); db.flush(); payload={'decision_id':d.id,'business_id':bid,'twin_version':b.twin_version,'result':result}; ledger=DecisionLedger(tenant_id=u.tenant_id,business_id=bid,decision_id=d.id,payload_hash=decision_hash(payload),payload_json=json.dumps(payload)); db.add(ledger); audit(db,u,'board_run','decision',d.id,{'risk_tier':risk,'confidence':result['confidence'],'ledger_hash':ledger.payload_hash}); db.commit(); return {'decision_id':d.id,'risk_tier':risk,'board':result,'ledger_hash':ledger.payload_hash}
@app.get('/api/businesses/{bid}/command-center')
def command_center(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    b=business_for(db,bid,u); twin=json.loads(b.twin_json or '{}'); ev=db.scalars(select(Evidence).where(Evidence.tenant_id==u.tenant_id,Evidence.business_id==bid)).all(); dec=db.scalars(select(Decision).where(Decision.tenant_id==u.tenant_id,Decision.business_id==bid).order_by(Decision.created_at.desc()).limit(10)).all(); tenant=db.get(Tenant,u.tenant_id); return {'business':{'id':b.id,'name':b.name,'state':b.lifecycle_state,'twin_version':b.twin_version},'financials':financial_model(twin),'twin':twin,'evidence_count':len(ev),'recent_decisions':[{'id':d.id,'question':d.question,'risk_tier':d.risk_tier,'status':d.status} for d in dec],'security':{'lockdown':tenant.lockdown,'autonomous_tier4':False,'tenant_isolation':True}}

@app.get('/api/session/bootstrap')
def session_bootstrap(request:Request, rec:SessionRecord=Depends(current_session)):
    csrf=request.cookies.get(CSRF_COOKIE)
    if not csrf or token_hash(csrf)!=rec.csrf_hash: raise HTTPException(401,'Session bootstrap failed')
    return {'csrf':csrf}

@app.post('/api/founder-dna')
def save_founder_dna(x:FounderProfileIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    ensure_not_lockdown(db,u)
    prev=db.scalars(select(FounderProfile).where(FounderProfile.tenant_id==u.tenant_id,FounderProfile.user_id==u.id).order_by(FounderProfile.version.desc())).first()
    v=(prev.version+1) if prev else 1
    p=FounderProfile(tenant_id=u.tenant_id,user_id=u.id,version=v,profile_json=json.dumps(x.profile)); db.add(p); db.flush()
    audit(db,u,'save','founder_profile',p.id,{'version':v}); db.commit()
    return {'id':p.id,'version':v,'profile':x.profile,'dna':founder_score(x.profile)}
@app.get('/api/founder-dna')
def get_founder_dna(u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.scalars(select(FounderProfile).where(FounderProfile.tenant_id==u.tenant_id,FounderProfile.user_id==u.id).order_by(FounderProfile.version.desc())).first()
    if not p:return {'profile':{},'dna':{}}
    profile=json.loads(p.profile_json); return {'id':p.id,'version':p.version,'profile':profile,'dna':founder_score(profile)}
@app.get('/api/businesses/{bid}/battle')
def battle(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    b=business_for(db,bid,u); return {'scenarios':battle_mode(json.loads(b.twin_json or '{}'))}
@app.get('/api/businesses/{bid}/failure-lab')
def failure(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    b=business_for(db,bid,u); return {'scenarios':failure_lab(json.loads(b.twin_json or '{}'))}
@app.post('/api/businesses/{bid}/execution')
def create_execution(bid:str,x:ExecutionGenerateIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    ensure_not_lockdown(db,u); business_for(db,bid,u); items=execution_plan(x.goal,x.budget)
    for i in items: db.add(ExecutionTask(id=i['id'],tenant_id=u.tenant_id,business_id=bid,horizon=i['horizon'],task=i['task'],budget=str(i['budget']),status=i['status'],kpi=i['kpi']))
    audit(db,u,'generate','execution_plan',bid,{'tasks':len(items)}); db.commit(); return {'tasks':items}
@app.get('/api/businesses/{bid}/execution')
def get_execution(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    business_for(db,bid,u); xs=db.scalars(select(ExecutionTask).where(ExecutionTask.tenant_id==u.tenant_id,ExecutionTask.business_id==bid)).all()
    return [{'id':x.id,'horizon':x.horizon,'task':x.task,'budget':float(x.budget),'status':x.status,'kpi':x.kpi} for x in xs]
@app.patch('/api/businesses/{bid}/execution/{tid}')
def update_task(bid:str,tid:str,x:TaskStatusIn,u:User=Depends(current_user),db:Session=Depends(get_db)):
    ensure_not_lockdown(db,u); business_for(db,bid,u); task=db.scalar(select(ExecutionTask).where(ExecutionTask.id==tid,ExecutionTask.tenant_id==u.tenant_id,ExecutionTask.business_id==bid))
    if not task: raise HTTPException(404,'Task not found')
    task.status=x.status; audit(db,u,'update','execution_task',tid,{'status':x.status}); db.commit(); return {'ok':True,'status':x.status}
@app.get('/api/businesses/{bid}/plan-vs-actual')
def plan_actual(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    b=business_for(db,bid,u); actuals=db.scalars(select(ActualObservation).where(ActualObservation.tenant_id==u.tenant_id,ActualObservation.business_id==bid)).all()
    return {'variance':variance_report(json.loads(b.twin_json or '{}'),[{'key':a.key,'value':a.value} for a in actuals])}
@app.get('/api/businesses/{bid}/decision-ledger')
def decision_ledger(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    business_for(db,bid,u); xs=db.scalars(select(DecisionLedger).where(DecisionLedger.tenant_id==u.tenant_id,DecisionLedger.business_id==bid).order_by(DecisionLedger.created_at.desc())).all()
    return [{'decision_id':x.decision_id,'hash':x.payload_hash,'created_at':x.created_at,'payload':json.loads(x.payload_json)} for x in xs]

@app.get('/api/community')
def community_feed(category:str|None=None,u:User=Depends(current_user),db:Session=Depends(get_db)):
    blocked=set(db.scalars(select(CommunityBlock.blocked_user_id).where(CommunityBlock.blocker_user_id==u.id)).all())
    q=select(CommunityPost).where(CommunityPost.deleted==False,CommunityPost.moderation_status=='visible').order_by(CommunityPost.created_at.desc()).limit(100)
    if category: q=q.where(CommunityPost.category==category.upper())
    xs=[x for x in db.scalars(q).all() if x.user_id not in blocked]
    return [{'id':x.id,'display_name':x.display_name,'category':x.category,'body':x.body,'created_at':x.created_at,'is_mine':x.user_id==u.id} for x in xs]

@app.post('/api/community')
def community_create(x:CommunityPostIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); allowed={'ASK','WIN','EXPERIENCE','CONNECT'}; cat=x.category.upper()
    if cat not in allowed: raise HTTPException(400,'Invalid category')
    p=CommunityPost(tenant_id=u.tenant_id,user_id=u.id,display_name=x.display_name,category=cat,body=x.body)
    db.add(p); db.flush(); audit(db,u,'create','community_post',p.id,{'category':cat}); db.commit(); db.refresh(p)
    return {'id':p.id,'category':p.category,'body':p.body}

@app.get('/api/community/{post_id}/replies')
def community_replies(post_id:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    p=db.get(CommunityPost,post_id)
    if not p or p.deleted or p.moderation_status!='visible': raise HTTPException(404,'Post not found')
    blocked=set(db.scalars(select(CommunityBlock.blocked_user_id).where(CommunityBlock.blocker_user_id==u.id)).all())
    xs=db.scalars(select(CommunityReply).where(CommunityReply.post_id==post_id,CommunityReply.deleted==False,CommunityReply.moderation_status=='visible').order_by(CommunityReply.created_at.asc())).all()
    return [{'id':x.id,'display_name':x.display_name,'body':x.body,'created_at':x.created_at} for x in xs if x.user_id not in blocked]

@app.post('/api/community/{post_id}/replies')
def community_reply(post_id:str,x:CommunityReplyIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); p=db.get(CommunityPost,post_id)
    if not p or p.deleted or p.moderation_status!='visible': raise HTTPException(404,'Post not found')
    r=CommunityReply(post_id=post_id,tenant_id=u.tenant_id,user_id=u.id,display_name=x.display_name,body=x.body)
    db.add(r); db.flush(); audit(db,u,'create','community_reply',r.id,{'post_id':post_id}); db.commit(); db.refresh(r)
    return {'id':r.id,'body':r.body}

@app.post('/api/community/{post_id}/report')
def community_report(post_id:str,x:CommunityReportIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    p=db.get(CommunityPost,post_id)
    if not p or p.deleted: raise HTTPException(404,'Post not found')
    r=CommunityReport(reporter_user_id=u.id,target_type='post',target_id=post_id,reason=x.reason)
    db.add(r); db.flush(); audit(db,u,'report','community_post',post_id,{'report_id':r.id}); db.commit()
    return {'ok':True,'report_id':r.id}

@app.post('/api/community/block')
def community_block(x:CommunityBlockIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    if x.blocked_user_id==u.id: raise HTTPException(400,'Cannot block yourself')
    existing=db.scalar(select(CommunityBlock).where(CommunityBlock.blocker_user_id==u.id,CommunityBlock.blocked_user_id==x.blocked_user_id))
    if not existing: db.add(CommunityBlock(blocker_user_id=u.id,blocked_user_id=x.blocked_user_id))
    audit(db,u,'block','community_user',x.blocked_user_id); db.commit(); return {'ok':True}

@app.post('/api/community/{post_id}/block-author')
def community_block_author(post_id:str,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    p=db.get(CommunityPost,post_id)
    if not p or p.deleted or p.moderation_status!='visible': raise HTTPException(404,'Post not found')
    if p.user_id==u.id: raise HTTPException(400,'Cannot block yourself')
    existing=db.scalar(select(CommunityBlock).where(CommunityBlock.blocker_user_id==u.id,CommunityBlock.blocked_user_id==p.user_id))
    if not existing: db.add(CommunityBlock(blocker_user_id=u.id,blocked_user_id=p.user_id))
    audit(db,u,'block','community_user',p.user_id,{'source_post_id':post_id}); db.commit(); return {'ok':True}

@app.delete('/api/community/{post_id}')
def community_delete(post_id:str,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); p=db.get(CommunityPost,post_id)
    if not p or p.user_id!=u.id: raise HTTPException(404,'Post not found')
    p.deleted=True; audit(db,u,'delete','community_post',post_id); db.commit(); return {'ok':True}

# --- Genesis Route / Proof / Reroute API ---
from .route_engine import GenesisRouteEngine, FounderReality, DestinationContract
_route_engine=GenesisRouteEngine()
def _rr(x): return FounderReality(**x.model_dump())
def _dd(x): return DestinationContract(**x.model_dump())

@app.post('/api/route/portfolio')
def route_portfolio(x:RoutePortfolioIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); result=_route_engine.route_portfolio(_rr(x.reality),_dd(x.destination)); audit(db,u,'calculate','route_portfolio','current',{'routes':len(result)}); db.commit(); return {'routes':result}
@app.post('/api/route/next-turn')
def route_next_turn(x:RouteNextTurnIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    result=_route_engine.next_turn(_rr(x.reality),_dd(x.destination),x.proofs); audit(db,u,'calculate','next_turn','current',{'checkpoint':result.get('checkpoint')}); db.commit(); return result
@app.post('/api/route/reroute')
def route_reroute(x:RouteRerouteIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); result=_route_engine.reroute(_rr(x.old_reality),_rr(x.new_reality),_dd(x.destination)); audit(db,u,'reroute','business_route','current',{'changed':result['changed']}); db.commit(); return result
@app.post('/api/route/counterfactual')
def route_counterfactual(x:CounterfactualIn,u:User=Depends(current_user)):
    return _route_engine.counterfactual_requirements(_dd(x.destination),x.avg_ticket,x.gross_margin,x.close_rate)

@app.post('/api/route/evolution')
def route_evolution(x:EvolutionIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    metrics={'monthly_revenue':x.monthly_revenue,'repeat_customer_share':x.repeat_customer_share,'gross_margin':x.gross_margin,'capacity_used':x.capacity_used}
    result=_route_engine.evolution(_rr(x.reality),_dd(x.destination),metrics)
    audit(db,u,'calculate','business_evolution','current',{'generation':result['generation'],'recommended':result['recommended_evolution']['key']}); db.commit(); return result


@app.get('/api/execution/catalog')
def execution_catalog(u:User=Depends(current_user)):
    return {'points':public_catalog()}

@app.get('/api/businesses/{bid}/actions')
def execution_actions(bid:str,u:User=Depends(current_user),db:Session=Depends(get_db)):
    business_for(db,bid,u)
    rows=db.scalars(select(ExecutionActionRecord).where(ExecutionActionRecord.tenant_id==u.tenant_id,ExecutionActionRecord.business_id==bid).order_by(ExecutionActionRecord.created_at.desc())).all()
    return [{'id':r.id,'point_key':r.point_key,'mode':r.mode,'risk_tier':r.risk_tier,'status':r.status,'result':json.loads(r.result_json or '{}'),'created_at':r.created_at} for r in rows]

@app.post('/api/execution/actions')
def propose_execution(x:ExecutionProposeIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); business_for(db,x.business_id,u)
    point=CATALOG.get(x.point_key)
    if not point: raise HTTPException(404,'Unknown execution point')
    if point.risk_tier==4 and point.mode=='EXECUTE': raise HTTPException(403,'Tier-4 autonomous execution is disabled')
    status='AWAITING_APPROVAL' if point.risk_tier>=2 else 'PROPOSED'
    a=ExecutionActionRecord(tenant_id=u.tenant_id,business_id=x.business_id,user_id=u.id,point_key=point.key,mode=point.mode,risk_tier=point.risk_tier,status=status,payload_json=json.dumps(x.payload),idempotency_key=secrets.token_urlsafe(24))
    db.add(a); db.flush(); audit(db,u,'propose','execution_action',a.id,{'point':point.key,'mode':point.mode,'risk_tier':point.risk_tier}); db.commit()
    return {'id':a.id,'status':a.status,'mode':a.mode,'risk_tier':a.risk_tier,'connection':connection_status(point)}

@app.post('/api/execution/actions/{aid}/approve')
def approve_execution(aid:str,x:ExecutionApproveIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); a=ensure_tenant(db.get(ExecutionActionRecord,aid),u)
    if not x.confirm: raise HTTPException(400,'Explicit confirmation required')
    if a.risk_tier>=3 and u.role not in ('owner','admin'): raise HTTPException(403,'Owner/admin approval required')
    a.approved_by=u.id; a.status='APPROVED'; audit(db,u,'approve','execution_action',a.id,{'point':a.point_key}); db.commit(); return {'id':a.id,'status':a.status}

@app.post('/api/execution/actions/{aid}/perform')
async def perform_execution(aid:str,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); a=ensure_tenant(db.get(ExecutionActionRecord,aid),u); point=CATALOG.get(a.point_key)
    if not point: raise HTTPException(409,'Execution point no longer available')
    if a.status in ('EXECUTED','PREPARED','GUIDED','VERIFIED'): return {'id':a.id,'status':a.status,'result':json.loads(a.result_json or '{}'),'replayed':True}
    if a.risk_tier>=2 and a.status!='APPROVED': raise HTTPException(403,'Explicit approval required before this action')
    payload=json.loads(a.payload_json or '{}')
    try:
        if point.mode=='PREPARE':
            result=prepare_execution(point,payload); a.status='PREPARED'
            db.add(ExecutionReceiptRecord(tenant_id=u.tenant_id,business_id=a.business_id,action_id=a.id,evidence_type='artifact',summary='Genesis generated the requested artifact',external_reference=None,metadata_json=json.dumps({'artifact_type':result.get('artifact_type')}),provenance='SYSTEM',trusted=True))
        elif point.mode=='GUIDE':
            result={'official_url':point.official_url,'provider':point.provider,'notice':'Complete this action on the verified official destination. Genesis does not claim it was filed or submitted.'}; a.status='GUIDED'
        else:
            # External dispatch is locally at-most-once. Once started, an ambiguous outcome
            # must be reconciled; Genesis will not blindly re-send it.
            if a.dispatch_started_at is not None:
                raise RuntimeError('AMBIGUOUS_PROVIDER_TIMEOUT: dispatch already attempted; reconcile before retry')
            a.dispatch_started_at=datetime.now(timezone.utc); db.commit()
            result=await execute_provider(point,payload,a.idempotency_key); a.status='EXECUTED'
            a.provider_reference=result.get('external_reference')
            for k,v in (result.get('evidence') or {}).items():
                if v is not None: db.add(ExecutionReceiptRecord(tenant_id=u.tenant_id,business_id=a.business_id,action_id=a.id,evidence_type=k,summary=f'{point.provider} returned {k}',external_reference=str(v),metadata_json=json.dumps({'provider':point.provider}),provenance='PROVIDER',trusted=True))
        a.result_json=json.dumps(result); audit(db,u,'perform','execution_action',a.id,{'point':point.key,'status':a.status}); db.commit(); return {'id':a.id,'status':a.status,'result':result}
    except (RuntimeError,ValueError,KeyError) as e:
        a.status='NEEDS_RECONCILIATION' if str(e).startswith('AMBIGUOUS_PROVIDER_TIMEOUT') else 'FAILED'; a.result_json=json.dumps({'error':str(e)}); audit(db,u,'execution_failed','execution_action',a.id,{'point':point.key,'error':str(e)}); db.commit(); raise HTTPException(503,str(e))

@app.post('/api/execution/actions/{aid}/evidence')
def add_execution_evidence(aid:str,x:ExecutionEvidenceIn,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    a=ensure_tenant(db.get(ExecutionActionRecord,aid),u); business_for(db,a.business_id,u)
    point=CATALOG.get(a.point_key)
    if not point: raise HTTPException(409,'Execution point no longer available')
    # Users may add supporting evidence, but cannot mint provider/system proof.
    if x.evidence_type in set(point.expected_evidence) and point.mode=='EXECUTE':
        raise HTTPException(403,'Provider evidence cannot be self-asserted')
    trusted=False; provenance='USER'
    if point.mode=='GUIDE' and x.evidence_type=='user_confirmation':
        if a.status!='GUIDED' or not x.external_reference:
            raise HTTPException(422,'Guided completion confirmation requires the official confirmation/reference')
        trusted=True; provenance='USER_CONFIRMED_OFFICIAL'
    r=ExecutionReceiptRecord(tenant_id=u.tenant_id,business_id=a.business_id,action_id=a.id,evidence_type=x.evidence_type,summary=x.summary,external_reference=x.external_reference,metadata_json=json.dumps(x.metadata),provenance=provenance,trusted=trusted); db.add(r); db.flush(); audit(db,u,'evidence','execution_action',a.id,{'type':x.evidence_type,'provenance':'USER','trusted':False}); db.commit(); return {'receipt_id':r.id,'trusted':trusted,'provenance':provenance}

@app.post('/api/execution/actions/{aid}/verify')
def verify_execution(aid:str,u:User=Depends(current_user),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    a=ensure_tenant(db.get(ExecutionActionRecord,aid),u); point=CATALOG.get(a.point_key)
    if not point: raise HTTPException(409,'Execution point no longer available')
    allowed_terminal={'EXECUTED','PREPARED','GUIDED'}
    if a.status not in allowed_terminal:
        raise HTTPException(409,{'message':'Action must be performed before verification','status':a.status})
    rows=db.scalars(select(ExecutionReceiptRecord).where(ExecutionReceiptRecord.tenant_id==u.tenant_id,ExecutionReceiptRecord.action_id==a.id)).all()
    trusted_got={r.evidence_type for r in rows if r.trusted}
    all_got={r.evidence_type for r in rows}
    # EXECUTE evidence must come from provider/system. PREPARE/GUIDE may use system-created
    # or user confirmation respectively, but self-asserted provider proof is never trusted.
    required=set(point.expected_evidence)
    got=trusted_got
    missing=sorted(required-got)
    if missing: raise HTTPException(409,{'message':'Trusted evidence required before verification','missing':missing})
    a.status='VERIFIED'
    feedback=_apply_execution_feedback(db,u,a,point,rows)
    audit(db,u,'verify','execution_action',a.id,{'evidence':sorted(got),'feedback':feedback}); db.commit()
    return {'id':a.id,'status':'VERIFIED','evidence':sorted(got),'business_feedback':feedback}

def _apply_execution_feedback(db:Session,u:User,a:ExecutionActionRecord,point,receipts:list[ExecutionReceiptRecord]):
    b=business_for(db,a.business_id,u)
    proofs=json.loads(b.proof_state_json or '{}')
    # Conservative mapping: execution proves only facts the action actually establishes.
    mapping={
      'email_send':['outreach sent'],
      'crm_customer_create':['customer record created'],
      'payment_link_create':['payment workflow ready'],
      'business_plan_prepare':['business plan prepared'],
      'offer_prepare':['offer prepared'],
      'outreach_prepare':['outreach prepared'],
      'pricing_prepare':['pricing prepared'],
      'launch_checklist_prepare':['launch checklist prepared'],
    }
    for proof in mapping.get(point.key,[]): proofs[proof]=True
    b.proof_state_json=json.dumps(proofs)
    ctx=json.loads(b.route_context_json or '{}')
    next_turn={'action':'Capture the real-world outcome of this verified action','proofs_recorded':mapping.get(point.key,[]),'route_recalculation':'pending route context'}
    # If route context has the required deterministic inputs, calculate a real next turn.
    try:
        rr=ctx.get('reality'); dd=ctx.get('destination')
        if rr and dd:
            next_turn=_route_engine.next_turn(FounderReality(**rr),DestinationContract(**dd),proofs)
    except (TypeError,ValueError,KeyError):
        next_turn={'action':'Review route inputs and capture the real-world outcome','proofs_recorded':mapping.get(point.key,[]),'route_recalculation':'route context invalid'}
    b.next_turn_json=json.dumps(next_turn); b.twin_version+=1
    return {'proof_state':proofs,'next_turn':next_turn,'twin_version':b.twin_version}

@app.post('/api/execution/actions/{aid}/reconcile')
def reconcile_execution(aid:str,x:ExecutionReconcileIn,u:User=Depends(require_owner),db:Session=Depends(get_db),_:bool=Depends(require_csrf)):
    ensure_not_lockdown(db,u); a=ensure_tenant(db.get(ExecutionActionRecord,aid),u); point=CATALOG.get(a.point_key)
    if a.status!='NEEDS_RECONCILIATION': raise HTTPException(409,'Action is not awaiting reconciliation')
    if x.outcome=='unknown':
        audit(db,u,'reconcile_unknown','execution_action',a.id,{'note':x.note}); db.commit()
        return {'id':a.id,'status':a.status,'retry_allowed':False}
    if x.outcome=='confirmed_failure':
        a.status='FAILED'; audit(db,u,'reconcile_failure','execution_action',a.id,{'note':x.note}); db.commit()
        return {'id':a.id,'status':a.status,'retry_allowed':False,'new_action_required':True}
    if not x.external_reference: raise HTTPException(422,'External reference required for confirmed success')
    a.status='EXECUTED'; a.provider_reference=x.external_reference
    for ev in point.expected_evidence:
        db.add(ExecutionReceiptRecord(tenant_id=u.tenant_id,business_id=a.business_id,action_id=a.id,evidence_type=ev,summary='Owner reconciliation confirmed against provider record',external_reference=x.external_reference,metadata_json=json.dumps({'provider':point.provider,'reconciled':True,'note':x.note}),provenance='RECONCILED_PROVIDER',trusted=True))
    audit(db,u,'reconcile_success','execution_action',a.id,{'external_reference':x.external_reference}); db.commit()
    return {'id':a.id,'status':a.status,'retry_allowed':False}

@app.post('/api/providers/square/webhook')
async def square_webhook(request:Request,db:Session=Depends(get_db)):
    body=await request.body(); sig=request.headers.get('x-square-hmacsha256-signature','')
    key=os.getenv('GENESIS_SQUARE_WEBHOOK_SIGNATURE_KEY','')
    notification_url=os.getenv('GENESIS_SQUARE_WEBHOOK_URL','')
    if not key or not notification_url: raise HTTPException(503,'Square webhook verification is not configured')
    expected=hmac.new(key.encode(),notification_url.encode()+body,hashlib.sha256).digest()
    import base64
    if not hmac.compare_digest(base64.b64encode(expected).decode(),sig): raise HTTPException(401,'Invalid webhook signature')
    payload=json.loads(body); event_id=str(payload.get('event_id') or payload.get('eventId') or '')
    if not event_id: raise HTTPException(422,'Missing event id')
    existing=db.scalar(select(ProviderWebhookEvent).where(ProviderWebhookEvent.provider=='square',ProviderWebhookEvent.event_id==event_id))
    if existing: return {'accepted':True,'duplicate':True}
    ev=ProviderWebhookEvent(provider='square',event_id=event_id,event_type=str(payload.get('type','unknown')),verified_signature=True,payload_hash=hashlib.sha256(body).hexdigest())
    db.add(ev); db.commit(); return {'accepted':True,'duplicate':False}
