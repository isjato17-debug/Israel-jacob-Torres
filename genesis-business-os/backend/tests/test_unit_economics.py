from decimal import Decimal
import pytest
from app.services.unit_economics import report, workflow_cost, customer_cost


def test_research_model_reproducible_and_no_actual_spend():
    assert report()==report()
    assert len(report()["scenarios"])==48
    assert all(row["actual_external_spending"]==0 for row in report()["scenarios"])


def test_token_cache_retries_and_extreme_usage_reveal_exposure():
    assert workflow_cost("advanced")["total"] > workflow_cost("economy")["total"]
    # Cache creation/storage can exceed read savings when recreated every attempt.
    assert workflow_cost("economy")["cache_creation"] > 0
    assert workflow_cost("economy")["inference"] > workflow_cost("economy",cached_fraction=Decimal(0))["inference"]
    assert workflow_cost("economy",attempts=Decimal(2))["inference"] > workflow_cost("economy")["inference"]
    assert customer_cost("operate","extreme","advanced")["unsustainable"]
    value=customer_cost("build","typical","balanced")
    assert value["contribution_margin"]>value["estimated_operating_profit_before_tax"]


def test_invalid_simulation_assumptions_fail_explicitly():
    with pytest.raises(ValueError):
        workflow_cost("economy",success_rate=Decimal(0))
