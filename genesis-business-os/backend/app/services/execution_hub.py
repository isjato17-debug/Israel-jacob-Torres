import os, secrets
from dataclasses import dataclass
from typing import Any
import httpx
from .provider_status import status as provider_status, record_verification

@dataclass(frozen=True)
class ExecutionPoint:
    key:str; title:str; mode:str; risk_tier:int; provider:str; capability:str
    expected_evidence:list[str]; official_url:str|None=None; credential_env:list[str]|None=None

CATALOG={p.key:p for p in [
    ExecutionPoint('email_send','Send customer/outreach email','EXECUTE',3,'sendgrid','mail.send',['provider_acceptance'],credential_env=['GENESIS_SENDGRID_API_KEY','GENESIS_SENDGRID_FROM_EMAIL']),
    ExecutionPoint('crm_customer_create','Create CRM/customer record','EXECUTE',2,'square','customers.create',['provider_object_id'],credential_env=['GENESIS_SQUARE_ACCESS_TOKEN']),
    ExecutionPoint('payment_link_create','Create customer payment link','EXECUTE',3,'square','checkout.payment_link.create',['payment_link','provider_object_id'],credential_env=['GENESIS_SQUARE_ACCESS_TOKEN','GENESIS_SQUARE_LOCATION_ID']),
    ExecutionPoint('ein_apply','Apply for an EIN','GUIDE',4,'irs','ein.apply',['user_confirmation'],'https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number'),
    ExecutionPoint('business_launch_requirements','Review registration/licenses/permits','GUIDE',2,'sba','business.launch',['user_confirmation'],'https://www.sba.gov/counseling/launch-your-business/'),
    ExecutionPoint('business_plan_prepare','Prepare business plan','PREPARE',1,'genesis','document.business_plan',['artifact']),
    ExecutionPoint('offer_prepare','Prepare customer offer','PREPARE',1,'genesis','sales.offer',['artifact']),
    ExecutionPoint('outreach_prepare','Prepare outreach campaign','PREPARE',1,'genesis','sales.outreach',['artifact']),
    ExecutionPoint('pricing_prepare','Prepare pricing model','PREPARE',1,'genesis','finance.pricing',['artifact']),
    ExecutionPoint('launch_checklist_prepare','Prepare launch checklist','PREPARE',1,'genesis','operations.launch_checklist',['artifact']),
]}

def connection_status(p:ExecutionPoint):
    if p.mode!='EXECUTE': return {'state':'READY','missing':[]}
    return provider_status(p.key, p.credential_env or [])

def public_catalog():
    return [{**p.__dict__,'connection':connection_status(p)} for p in CATALOG.values()]

def prepare(point:ExecutionPoint,payload:dict[str,Any]):
    if point.key=='business_plan_prepare':
        name=payload.get('business_name','Your Business'); goal=payload.get('goal','Build a profitable, validated business')
        text=f'''# {name} — Business Plan\n\n## Goal\n{goal}\n\n## Customer\n{payload.get('customer','Define the narrowest customer with an urgent problem.')}\n\n## Offer\n{payload.get('offer','Start with one clear outcome-focused offer.')}\n\n## Validation\nTalk to at least 3 qualified prospects and record explicit buying signals before major spending.\n\n## Economics\nPrice: {payload.get('price','TBD')}\nProtected reserve: {payload.get('reserve','TBD')}\nRisk capital: {payload.get('risk_capital','TBD')}\n\n## Next Move\n{payload.get('next_move','Get the first paying customer and record actual revenue, cost and delivery time.')}\n'''
    elif point.key=='offer_prepare':
        text=f"Offer: {payload.get('service','Service')} for {payload.get('customer','target customer')} — {payload.get('outcome','a clear measurable result')} for {payload.get('price','a validated price')}. Proof before scale: obtain explicit buying signals and paid transactions."
    elif point.key=='outreach_prepare':
        text=f"Subject: {payload.get('subject','Quick question')}\n\nHi {payload.get('name','there')},\n\n{payload.get('message','I help customers like you solve a specific problem. Would you be open to a quick conversation to see if this is useful?')}\n\n{payload.get('sender','Founder')}"
    elif point.key=='pricing_prepare':
        cost=float(payload.get('unit_cost',0) or 0); margin=float(payload.get('target_margin',0.5) or .5)
        price=round(cost/(1-margin),2) if 0<=margin<1 else None
        text=f"Unit cost: ${cost:.2f}\nTarget gross margin: {margin:.0%}\nIndicative minimum price: ${price:.2f}" if price is not None else 'Invalid target margin.'
    else:
        text='Launch checklist\n1. Validate demand\n2. Confirm applicable registration/tax/license requirements\n3. Set pricing and payment workflow\n4. Prepare customer acquisition workflow\n5. Record first paid transaction\n6. Measure actual margin and delivery time\n7. Reroute from evidence.'
    return {'artifact_type':'text/markdown','content':text}

async def execute(point:ExecutionPoint,payload:dict[str,Any],idempotency_key:str):
    status=connection_status(point)
    # Existing approval/dispatch guards remain authoritative. A configured adapter may
    # attempt an explicitly approved operation; only its actual response verifies it.
    if status['state'] not in ('CONFIGURED','VERIFIED_CONNECTED'):
        raise RuntimeError('Provider is not available for execution')
    timeout=httpx.Timeout(15.0,connect=5.0)
    try:
      async with httpx.AsyncClient(timeout=timeout) as client:
        if point.key=='email_send':
            body={'personalizations':[{'to':[{'email':payload['to']}]}],'from':{'email':os.environ['GENESIS_SENDGRID_FROM_EMAIL']},'subject':payload['subject'],'content':[{'type':'text/plain','value':payload['body']}]}
            r=await client.post('https://api.sendgrid.com/v3/mail/send',headers={'Authorization':'Bearer '+os.environ['GENESIS_SENDGRID_API_KEY'],'Content-Type':'application/json'},json=body)
            if r.status_code not in (200,202):
                record_verification(point.key, point.credential_env or [], 'ERROR')
                raise RuntimeError(f'SendGrid rejected request ({r.status_code})')
            record_verification(point.key, point.credential_env or [], 'VERIFIED_CONNECTED', successful=True)
            return {'provider':'sendgrid','provider_status':r.status_code,'external_reference':r.headers.get('x-message-id'),'evidence':{'provider_acceptance':r.headers.get('x-message-id') or 'accepted'},'delivery_semantics':'local_at_most_once; ambiguous outcomes require reconciliation'}
        headers={'Authorization':'Bearer '+os.environ['GENESIS_SQUARE_ACCESS_TOKEN'],'Content-Type':'application/json','Square-Version':'2026-09-16'}
        if point.key=='crm_customer_create':
            body={k:payload[k] for k in ('given_name','family_name','company_name','email_address','phone_number','note') if payload.get(k)}; body['idempotency_key']=idempotency_key
            r=await client.post('https://connect.squareup.com/v2/customers',headers=headers,json=body)
            if r.status_code>=300:
                record_verification(point.key, point.credential_env or [], 'ERROR')
                raise RuntimeError(f'Square rejected request ({r.status_code})')
            obj=r.json().get('customer',{})
            if not obj.get('id'): raise RuntimeError('Square response missing customer evidence')
            record_verification(point.key, point.credential_env or [], 'VERIFIED_CONNECTED', successful=True)
            return {'provider':'square','provider_status':r.status_code,'external_reference':obj.get('id'),'evidence':{'provider_object_id':obj.get('id')}}
        if point.key=='payment_link_create':
            amount=int(payload['amount_cents']);
            if amount<1: raise ValueError('amount_cents must be positive')
            body={'idempotency_key':idempotency_key,'quick_pay':{'name':payload['name'],'price_money':{'amount':amount,'currency':payload.get('currency','USD')},'location_id':os.environ['GENESIS_SQUARE_LOCATION_ID']}}
            r=await client.post('https://connect.squareup.com/v2/online-checkout/payment-links',headers=headers,json=body)
            if r.status_code>=300:
                record_verification(point.key, point.credential_env or [], 'ERROR')
                raise RuntimeError(f'Square rejected request ({r.status_code})')
            obj=r.json().get('payment_link',{})
            if not obj.get('id') or not obj.get('url'): raise RuntimeError('Square response missing payment-link evidence')
            record_verification(point.key, point.credential_env or [], 'VERIFIED_CONNECTED', successful=True)
            return {'provider':'square','provider_status':r.status_code,'external_reference':obj.get('id'),'evidence':{'provider_object_id':obj.get('id'),'payment_link':obj.get('url')}}
      raise RuntimeError('Unsupported execution point')
    except httpx.TimeoutException as e:
      record_verification(point.key, point.credential_env or [], 'UNAVAILABLE')
      raise RuntimeError('AMBIGUOUS_PROVIDER_TIMEOUT: reconcile provider state before retry') from e
    except httpx.HTTPError as e:
      record_verification(point.key, point.credential_env or [], 'UNAVAILABLE')
      raise RuntimeError('PROVIDER_NETWORK_ERROR: external provider request failed') from e
