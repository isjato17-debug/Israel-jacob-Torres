
from models import *
from typing import Dict, Any, List

class PolicyError(Exception): pass
class VerificationError(Exception): pass

class ExecutionRegistry:
    def __init__(self):
        self.resources: Dict[str,ResourceTrustRecord]={}
        self.actions: Dict[str,ExecutionAction]={}
        self.receipts: Dict[str,List[EvidenceReceipt]]={}

    def register_resource(self, r: ResourceTrustRecord):
        self.resources[r.resource_id]=r

    def propose(self,title,mode,risk_tier,resource_id=None,expected_evidence=None,payload=None):
        if risk_tier not in range(0,5): raise ValueError("risk tier must be 0..4")
        if resource_id and resource_id not in self.resources: raise ValueError("unknown resource")
        if risk_tier==4 and mode==ActionMode.EXECUTE:
            raise PolicyError("Tier-4 autonomous execution is disabled.")
        a=ExecutionAction(
            action_id=uid("act"),title=title,mode=mode,risk_tier=risk_tier,
            resource_id=resource_id,status=ActionStatus.AWAITING_APPROVAL if risk_tier>=2 else ActionStatus.PROPOSED,
            user_approval_required=risk_tier>=2,expected_evidence=expected_evidence or [],payload=payload or {}
        )
        self.actions[a.action_id]=a; return a

    def approve(self, action_id:str, approved:bool):
        a=self.actions[action_id]
        if not approved:
            a.status=ActionStatus.FAILED; return a
        if a.risk_tier==4 and a.mode==ActionMode.EXECUTE:
            raise PolicyError("Tier-4 autonomous execution is disabled.")
        return a

    def perform_reference(self, action_id:str, approved:bool=False):
        """
        Reference dispatcher. Production adapters replace this method.
        It NEVER pretends an unavailable external integration succeeded.
        """
        a=self.actions[action_id]
        if a.user_approval_required and not approved: raise PolicyError("Explicit approval required.")
        resource=self.resources.get(a.resource_id) if a.resource_id else None
        if a.mode==ActionMode.EXECUTE:
            if not resource or resource.requires_connection:
                raise PolicyError("Live provider connection required; cannot claim execution.")
            a.status=ActionStatus.EXECUTED
        elif a.mode==ActionMode.PREPARE:
            a.status=ActionStatus.PREPARED
        else:
            if not resource or not resource.official_url:
                raise PolicyError("Verified destination required for guided action.")
            a.status=ActionStatus.GUIDED
        return a

    def add_evidence(self,action_id,evidence_type,summary,source,external_reference=None,metadata=None):
        a=self.actions[action_id]
        r=EvidenceReceipt(uid("rcpt"),action_id,evidence_type,summary,source,utcnow(),external_reference,metadata or {})
        self.receipts.setdefault(action_id,[]).append(r); return r

    def verify(self,action_id):
        a=self.actions[action_id]
        got={r.evidence_type for r in self.receipts.get(action_id,[])}
        missing=[x for x in a.expected_evidence if x not in got]
        if missing: raise VerificationError("Missing evidence: "+", ".join(missing))
        a.status=ActionStatus.VERIFIED
        return {"verified":True,"action":a,"receipts":self.receipts.get(action_id,[])}
