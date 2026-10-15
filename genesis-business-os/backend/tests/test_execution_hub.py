import os
from app.services.execution_hub import CATALOG, connection_status, prepare

def test_external_execution_never_claims_connected_without_secrets(monkeypatch):
    monkeypatch.delenv('GENESIS_SENDGRID_API_KEY',raising=False); monkeypatch.delenv('GENESIS_SENDGRID_FROM_EMAIL',raising=False)
    assert connection_status(CATALOG['email_send'])['state']=='NOT_CONFIGURED'

def test_government_action_is_guide_not_execute():
    p=CATALOG['ein_apply']; assert p.mode=='GUIDE' and p.risk_tier==4 and p.official_url.startswith('https://www.irs.gov/')

def test_prepare_produces_real_artifact():
    r=prepare(CATALOG['business_plan_prepare'],{'business_name':'Test Co','goal':'Get first customer'})
    assert r['artifact_type']=='text/markdown' and 'Test Co' in r['content'] and 'Get first customer' in r['content']

def test_square_payment_link_requires_server_credentials(monkeypatch):
    monkeypatch.delenv('GENESIS_SQUARE_ACCESS_TOKEN',raising=False); monkeypatch.delenv('GENESIS_SQUARE_LOCATION_ID',raising=False)
    s=connection_status(CATALOG['payment_link_create']); assert s['state']=='NOT_CONFIGURED' and len(s['missing'])==2
