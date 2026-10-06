
from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
import uuid

class ActionMode(str, Enum):
    EXECUTE="EXECUTE"
    PREPARE="PREPARE"
    GUIDE="GUIDE"

class ActionStatus(str, Enum):
    PROPOSED="PROPOSED"
    AWAITING_APPROVAL="AWAITING_APPROVAL"
    PREPARED="PREPARED"
    EXECUTED="EXECUTED"
    GUIDED="GUIDED"
    VERIFIED="VERIFIED"
    FAILED="FAILED"

@dataclass
class ResourceTrustRecord:
    resource_id: str
    name: str
    resource_type: str
    authority_level: str
    jurisdiction: str
    capabilities: List[str]
    requires_connection: bool
    official_url: Optional[str]=None
    checked_at: Optional[str]=None
    notes: str=""

@dataclass
class EvidenceReceipt:
    receipt_id: str
    action_id: str
    evidence_type: str
    summary: str
    source: str
    created_at: str
    external_reference: Optional[str]=None
    metadata: Dict[str,Any]=field(default_factory=dict)

@dataclass
class ExecutionAction:
    action_id: str
    title: str
    mode: ActionMode
    risk_tier: int
    resource_id: Optional[str]
    status: ActionStatus
    user_approval_required: bool
    expected_evidence: List[str]
    payload: Dict[str,Any]=field(default_factory=dict)

def utcnow(): return datetime.now(timezone.utc).isoformat()
def uid(prefix): return prefix+"_"+uuid.uuid4().hex[:16]
