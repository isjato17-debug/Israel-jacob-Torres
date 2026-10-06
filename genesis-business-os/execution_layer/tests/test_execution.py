
import sys
sys.path.insert(0,"app")
from models import *
from execution_engine import *
def test_no_fake_execute():
    x=ExecutionRegistry()
    x.register_resource(ResourceTrustRecord("email","Email Provider","provider","third-party","US",["send"],True))
    a=x.propose("Send campaign",ActionMode.EXECUTE,3,"email",["provider_receipt"])
    try: x.perform_reference(a.action_id,approved=True); assert False
    except PolicyError: pass
def test_proof_required():
    x=ExecutionRegistry()
    a=x.propose("Create offer",ActionMode.PREPARE,1,None,["artifact_hash"])
    x.perform_reference(a.action_id)
    try: x.verify(a.action_id); assert False
    except VerificationError: pass
    x.add_evidence(a.action_id,"artifact_hash","Offer generated","genesis")
    assert x.verify(a.action_id)["verified"]
def test_tier4_execute_disabled():
    x=ExecutionRegistry()
    try:
        x.propose("Sign contract",ActionMode.EXECUTE,4)
        assert False
    except PolicyError: pass
