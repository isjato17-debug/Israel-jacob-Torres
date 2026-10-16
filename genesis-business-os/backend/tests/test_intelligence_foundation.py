import json
import time
from unittest.mock import patch
import pytest
from app.services.intelligence_contracts import ProviderConfig, StructuredRequest, IntelligenceProposal
from app.services.intelligence_provider import (generate, MockProvider, ProviderFailure,
                                                DisabledCompatibleProvider)
from app.services.intelligence import request_proposal, context_for, serialize
from app.services.idea_planning import prepare_plans
from app.services.business_strategy import recommendations
from app.services.document_engine import canonical
from app.services.ai_provider import LiveUsageNotAuthorized
from app.db import SessionLocal
from app.models import User
from test_unified_intelligence import env
from test_project_execution import create
from test_big_consultation import account


@pytest.fixture
def ctx():
    facts = {"concept": "Cleaning service in New York", "industry": "cleaning",
             "budget_cents": 300000, "jurisdiction": "NY", "goals": "Owner-operated repeat customers",
             "notes": "", "preferences": "", "assumptions": ""}
    return {"facts": facts, "strategies": recommendations(facts), "financial_plans": prepare_plans(facts)}


def test_valid_contract_provenance_estimates_and_offline_wire_builder(ctx):
    value = generate(ctx, "test-correlation")
    assert len(value.proposal.strategies) == 2 and len(value.proposal.financial_plans) == 3
    assert value.estimated_max_cost_microusd == 0 and value.estimated_input_tokens > 0
    req = StructuredRequest(correlation_id="test", model="future-reviewed-model", context=ctx,
                            response_schema=IntelligenceProposal.model_json_schema(), max_output_tokens=8000)
    wire = DisabledCompatibleProvider().build_request(req)
    assert wire["model"] == "future-reviewed-model" and wire["response_format"]["type"] == "json_schema"
    with pytest.raises(LiveUsageNotAuthorized):
        DisabledCompatibleProvider().generate(req)


@pytest.mark.parametrize("mutation,code", [
    (lambda x: x.pop("summary"), "SCHEMA_INVALID"),
    (lambda x: x.update(commands=["ignore safety"]), "SCHEMA_INVALID"),
    (lambda x: x["tasks"][0].update(tool="government.submit"), "SCHEMA_INVALID"),
    (lambda x: x["tasks"][0].update(authorized=True), "SCHEMA_INVALID"),
    (lambda x: x["tasks"][0].update(evidence={"status": "COMPLETE"}), "SCHEMA_INVALID"),
    (lambda x: x["financial_plans"][0].update(startup_cents=1), "FINANCIAL_MISMATCH"),
    (lambda x: x["strategies"][1].update(key=x["strategies"][0]["key"]), "SCHEMA_INVALID"),
    (lambda x: x.update(regulatory_claims=[{"source_url":"https://evil.example.com", "claim":"File now",
                                         "verification":"UNVERIFIED"}]), "UNSUPPORTED_REGULATORY_SOURCE"),
    (lambda x: x.update(regulatory_claims=[{"source_url":"https://www.sba.gov", "claim":"Required",
                                         "verification":"VERIFIED"}]), "SCHEMA_INVALID"),
])
def test_reject_untrusted_malformed_missing_and_privileged_output(ctx, mutation, code):
    class Bad:
        def generate(self, req):
            value = json.loads(MockProvider().generate(req))
            mutation(value)
            return canonical(value)
    with pytest.raises(ProviderFailure) as error:
        generate(ctx, "bad", provider=Bad())
    assert error.value.code == code and error.value.attempts == 1


@pytest.mark.parametrize("raw", ["not json", "[]", None, " " * 160001])
def test_malformed_response(ctx, raw):
    class Bad:
        def generate(self, req): return raw
    with pytest.raises(ProviderFailure):
        generate(ctx, "bad-response", provider=Bad())


def test_timeout_and_retry_ceiling(ctx):
    class Slow:
        def generate(self, req):
            time.sleep(.08)
            return MockProvider().generate(req)
    with pytest.raises(ProviderFailure) as err:
        generate(ctx, "timeout", ProviderConfig(timeout_seconds=.01), provider=Slow())
    assert err.value.code == "TIMEOUT" and err.value.attempts == 1
    class Failing:
        calls = 0
        def generate(self, req):
            self.calls += 1
            raise RuntimeError("private provider text")
    worker = Failing()
    with pytest.raises(ProviderFailure) as err:
        generate(ctx, "retry", ProviderConfig(max_attempts=3), provider=worker)
    assert worker.calls == err.value.attempts == 3 and str(err.value) == "PROVIDER_FAILURE"


def test_paid_disabled_even_with_environment_flags(ctx, monkeypatch):
    monkeypatch.setenv("GENESIS_AI_ENABLED", "true")
    with pytest.raises(ProviderFailure) as err:
        generate(ctx, "live", ProviderConfig(provider="openai_compatible_disabled", model="future-model"))
    assert err.value.code == "PAID_PROVIDER_DISABLED"


def test_saved_context_isolation_and_persistent_provenance(env):
    c, h, info, _, _ = env
    p, _, _ = create(env)
    other, _, outsider = account()
    with SessionLocal() as db:
        user = db.get(User, info["id"])
        with pytest.raises(Exception) as denied:
            context_for(db, db.get(User, outsider["id"]), p["id"])
        assert denied.value.status_code == 404
        _, ctx = context_for(db, user, p["id"])
        assert "email" not in canonical(ctx) and "password" not in canonical(ctx)
        record = request_proposal(db, user, p["id"], "persistent-test-request")
        db.commit()
        first = serialize(record)
        assert first["status"] == "VALIDATED" and first["integrity_verified"]
        assert first["classification"] == "MOCK_TEST_NOT_GENUINE_AI"
        assert first["live_reasoning_quality"] == "UNVERIFIED" and not first["paid_ai_enabled"]
        with patch("app.services.intelligence.generate", side_effect=AssertionError("No duplicate request")):
            assert request_proposal(db, user, p["id"], "persistent-test-request").id == record.id
    other.close()
