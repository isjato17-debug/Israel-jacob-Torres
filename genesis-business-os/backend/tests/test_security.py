import os
os.environ['GENESIS_JWT_SECRET']='x'*40
from fastapi.testclient import TestClient
from app.main import app
client=TestClient(app)

def reg(name,email):
    r=client.post('/api/auth/register',json={'tenant_name':name,'email':email,'password':'VeryStrongPassword!123'}); assert r.status_code==200; return r.json()['token']
def test_auth_and_tenant_isolation():
    a=reg('A','a@example.com'); b=reg('B','b@example.com')
    ra=client.post('/api/businesses',headers={'Authorization':'Bearer '+a},json={'name':'A Biz','twin':{'cash':100}}); assert ra.status_code==200
    bid=ra.json()['id']
    rb=client.post('/api/decisions',headers={'Authorization':'Bearer '+b},json={'business_id':bid,'question':'Can I touch this?','risk_tier':2})
    assert rb.status_code==404

def test_lockdown_blocks_writes():
    t=reg('C','c@example.com'); h={'Authorization':'Bearer '+t}
    assert client.post('/api/security/lockdown',headers=h,json={'enabled':True}).status_code==200
    r=client.post('/api/businesses',headers=h,json={'name':'Blocked','twin':{}}); assert r.status_code==423
    assert client.post('/api/security/lockdown',headers=h,json={'enabled':False}).status_code==200

def test_tier4_no_capability():
    t=reg('D','d@example.com'); h={'Authorization':'Bearer '+t}
    b=client.post('/api/businesses',headers=h,json={'name':'D Biz','twin':{}}).json()
    d=client.post('/api/decisions',headers=h,json={'business_id':b['id'],'question':'Sign a binding contract?','risk_tier':4}).json()
    a=client.post(f"/api/decisions/{d['id']}/approve",headers=h,json={'confirm':True}); assert a.status_code==200; assert a.json()['capability'] is None
