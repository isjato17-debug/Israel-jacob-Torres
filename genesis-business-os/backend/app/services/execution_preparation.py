"""Map saved project context into the existing Execution Hub's local PREPARE tools."""
import json

from ..models import BusinessIdea
from .execution_hub import CATALOG, prepare

PREPARATIONS = ("business_plan_prepare", "offer_prepare", "outreach_prepare",
                "pricing_prepare", "launch_checklist_prepare")


def prepare_for_project(db, p, key):
    point = CATALOG[key]
    if point.mode != "PREPARE" or point.provider != "genesis":
        raise ValueError("Only existing local preparation tools are eligible")
    facts = json.loads(db.get(BusinessIdea, p.idea_id).facts_json)
    plan = json.loads(p.plan_json)
    strategy = plan.get("business_strategy", {})
    ticket = plan["average_ticket_cents"] / 100
    margin = plan["gross_margin"]
    payload = {
        "business_name": p.name, "goal": facts.get("goals") or facts["concept"],
        "customer": strategy.get("target") or plan["target_customers"],
        "offer": strategy.get("approach") or plan["strategy"], "service": facts["concept"],
        "outcome": "A proposed service scope to validate with the prospective customer",
        "price": f"${ticket:,.2f} selected-plan assumption, not a verified quote or approved customer price",
        "reserve": f"${plan['reserve_cents'] / 100:,.2f} planned, not reserved in a bank",
        "risk_capital": f"${p.budget_cents / 100:,.2f} stated budget; spending not authorized",
        "next_move": strategy.get("validation") or plan["marketing"],
        "subject": "Proposed cleaning service — scope and needs discussion"
                   if "clean" in facts["concept"].lower() else "Proposed service — scope and needs discussion",
        "name": "[Prospective customer]", "sender": "[Business representative — confirm before sending]",
        "message": f"We are preparing {facts['concept']}. Would you be open to discussing your needs "
                   "and a possible service scope? No engagement, price or service date is confirmed by this draft.",
        # Derived scenario values are explicitly disclosed below, never represented as actual costs.
        "unit_cost": round(ticket * (1 - margin), 2), "target_margin": margin,
    }
    return {"tool": key, "mode": "PREPARE", "scope": "INTERNAL_DRAFT_NOT_SENT_OR_PUBLISHED",
            "classification": "DETERMINISTIC_DRAFT_FROM_UNVERIFIED_SELECTED_PLAN",
            "input_basis": "Saved customer idea and explicitly selected plan/strategy. Cost and price are scenario "
                          "estimates, not quotes or verified actuals. Missing identities remain placeholders.",
            "source_plan": plan["key"], "source_strategy": strategy.get("key"),
            "artifact": prepare(point, payload)}
