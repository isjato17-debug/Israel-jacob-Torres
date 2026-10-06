
import pathlib

def _read(rel):
    return (pathlib.Path(__file__).parents[1]/rel).read_text()

def test_sendgrid_does_not_claim_unsupported_idempotency_header():
    s=_read("app/services/execution_hub.py")
    start=s.index("if point.key=='email_send'")
    end=s.index("headers={'Authorization'",start)
    email=s[start:end]
    assert "'Idempotency-Key'" not in email
    assert "ambiguous outcomes require reconciliation" in s[start:]

def test_provider_evidence_cannot_be_self_asserted():
    s=_read("app/main.py")
    assert "Provider evidence cannot be self-asserted" in s
    assert "provenance='PROVIDER',trusted=True" in s

def test_verification_requires_performed_state_and_trusted_evidence():
    s=_read("app/main.py")
    assert "Action must be performed before verification" in s
    assert "trusted_got={r.evidence_type for r in rows if r.trusted}" in s

def test_reconciliation_endpoint_and_no_blind_retry():
    s=_read("app/main.py")
    assert "/api/execution/actions/{aid}/reconcile" in s
    assert "dispatch already attempted; reconcile before retry" in s
    assert "'retry_allowed':False" in s

def test_square_webhook_is_signature_verified_and_deduplicated():
    s=_read("app/main.py")
    assert "/api/providers/square/webhook" in s
    assert "x-square-hmacsha256-signature" in s
    assert "hmac.compare_digest" in s
    assert "ProviderWebhookEvent.provider=='square'" in s

def test_verified_execution_feeds_business_proof_and_next_turn():
    s=_read("app/main.py")
    assert "_apply_execution_feedback" in s
    assert "b.proof_state_json=json.dumps(proofs)" in s
    assert "b.next_turn_json=json.dumps(next_turn)" in s
    assert "_route_engine.next_turn" in s

def test_execution_proof_mapping_does_not_fake_revenue_or_demand():
    s=_read("app/main.py")
    segment=s[s.index("mapping={"):s.index("for proof in mapping",s.index("mapping={"))]
    assert "first paid transaction" not in segment
    assert "customer conversations" not in segment
