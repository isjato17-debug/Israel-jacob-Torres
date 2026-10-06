from pydantic import BaseModel, EmailStr, Field
from typing import Any

class Register(BaseModel):
    tenant_name: str=Field(min_length=2,max_length=120)
    email: EmailStr
    password: str=Field(min_length=12,max_length=128)
class Login(BaseModel): email: EmailStr; password: str
class FounderIn(BaseModel): objective: str=Field(min_length=5,max_length=4000); constraints: dict[str,Any]={}
class BusinessIn(BaseModel): name: str=Field(min_length=2,max_length=160); twin: dict[str,Any]={}
class EvidenceIn(BaseModel): business_id:str; classification:str; value:str; source_ref:str='user'; confidence:int=Field(ge=0,le=100)
class DecisionIn(BaseModel): business_id:str; question:str=Field(min_length=5,max_length=4000); risk_tier:int=Field(ge=0,le=4)
class ApproveIn(BaseModel): confirm: bool
class LockdownIn(BaseModel): enabled: bool

class GenerateBusinessIn(BaseModel):
    objective: str=Field(min_length=5,max_length=4000)
    constraints: dict[str,Any]={}
class BoardRunIn(BaseModel):
    question: str=Field(min_length=5,max_length=4000)
class ActualIn(BaseModel):
    key: str=Field(min_length=1,max_length=120)
    value: float
class TwinPatchIn(BaseModel):
    patch: dict[str,Any]

class FounderProfileIn(BaseModel):
    profile: dict[str,Any]
class ExecutionGenerateIn(BaseModel):
    goal: str=Field(min_length=3,max_length=2000)
    budget: float=0
class TaskStatusIn(BaseModel):
    status: str=Field(pattern='^(todo|doing|done|blocked)$')

class CommunityPostIn(BaseModel):
    category: str='ASK'
    body: str=Field(min_length=1,max_length=2000)
    display_name: str=Field(default='Founder',min_length=1,max_length=80)
class CommunityReplyIn(BaseModel):
    body: str=Field(min_length=1,max_length=1500)
    display_name: str=Field(default='Founder',min_length=1,max_length=80)

class RouteRealityIn(BaseModel):
    cash: float=Field(ge=0,le=1_000_000_000)
    reserve_floor: float=Field(ge=0,le=1_000_000_000)
    hours_per_week: float=Field(gt=0,le=168)
    skills: list[str]=Field(default_factory=list,max_length=100)
    assets: list[str]=Field(default_factory=list,max_length=100)
    location: str=Field(default='',max_length=200)
class RouteDestinationIn(BaseModel):
    target_monthly_owner_income: float=Field(gt=0,le=1_000_000_000)
    horizon_months: int=Field(gt=0,le=240)
    max_risk_cash: float=Field(ge=0,le=1_000_000_000)
class RoutePortfolioIn(BaseModel):
    reality: RouteRealityIn
    destination: RouteDestinationIn
class RouteNextTurnIn(RoutePortfolioIn):
    proofs: dict[str,bool]={}
class RouteRerouteIn(BaseModel):
    old_reality: RouteRealityIn
    new_reality: RouteRealityIn
    destination: RouteDestinationIn
class CounterfactualIn(BaseModel):
    destination: RouteDestinationIn
    avg_ticket: float=Field(gt=0,le=1_000_000_000)
    gross_margin: float=Field(gt=0,le=1)
    close_rate: float=Field(gt=0,le=1)

class CommunityReportIn(BaseModel):
    reason: str=Field(min_length=3,max_length=500)
class CommunityBlockIn(BaseModel):
    blocked_user_id: str=Field(min_length=1,max_length=80)

class ExecutionProposeIn(BaseModel):
    business_id: str
    point_key: str=Field(min_length=2,max_length=80)
    payload: dict[str,Any]=Field(default_factory=dict)
class ExecutionApproveIn(BaseModel):
    confirm: bool
class ExecutionEvidenceIn(BaseModel):
    evidence_type: str=Field(min_length=2,max_length=80)
    summary: str=Field(min_length=1,max_length=2000)
    external_reference: str|None=Field(default=None,max_length=2000)
    metadata: dict[str,Any]=Field(default_factory=dict)

class ExecutionReconcileIn(BaseModel):
    outcome: str=Field(pattern='^(confirmed_success|confirmed_failure|unknown)$')
    external_reference: str|None=Field(default=None,max_length=2000)
    note: str=Field(default='',max_length=2000)
class SquareWebhookIn(BaseModel):
    payload: dict[str,Any]=Field(default_factory=dict)

class EvolutionIn(RoutePortfolioIn):
    monthly_revenue: float=Field(default=0,ge=0,le=1_000_000_000)
    repeat_customer_share: float=Field(default=0,ge=0,le=1)
    gross_margin: float=Field(default=.5,ge=0,le=1)
    capacity_used: float=Field(default=.5,ge=0,le=1)
