import os
os.environ['GENESIS_JWT_SECRET']='x'*40
from fastapi.testclient import TestClient
from app.main import app
def register(client,name,email):
    r=client.post('/api/auth/register',json={'tenant_name':name,'email':email,'password':'VeryStrongPassword!123'})
    assert r.status_code==200, r.text
    return {'X-CSRF-Token':r.json()['csrf']}

def test_auth_and_tenant_isolation():
    client_a=TestClient(app); client_b=TestClient(app)
    headers_a=register(client_a,'A','a@example.com')
    headers_b=register(client_b,'B','b@example.com')
    ra=client_a.post('/api/businesses',headers=headers_a,json={'name':'A Biz','twin':{'cash':100}}); assert ra.status_code==200
    bid=ra.json()['id']
    rb=client_b.post('/api/decisions',headers=headers_b,json={'business_id':bid,'question':'Can I touch this?','risk_tier':2})
    assert rb.status_code==404

def test_lockdown_blocks_writes():
    client=TestClient(app); headers=register(client,'C','c@example.com')
    assert client.post('/api/security/lockdown',headers=headers,json={'enabled':True}).status_code==200
    r=client.post('/api/businesses',headers=headers,json={'name':'Blocked','twin':{}}); assert r.status_code==423
    assert client.post('/api/security/lockdown',headers=headers,json={'enabled':False}).status_code==200

def test_tier4_no_capability():
    client=TestClient(app); headers=register(client,'D','d@example.com')
    b=client.post('/api/businesses',headers=headers,json={'name':'D Biz','twin':{}}).json()
    d=client.post('/api/decisions',headers=headers,json={'business_id':b['id'],'question':'Sign a binding contract?','risk_tier':4}).json()
    a=client.post(f"/api/decisions/{d['id']}/approve",headers=headers,json={'confirm':True}); assert a.status_code==200; assert a.json()['capability'] is None
