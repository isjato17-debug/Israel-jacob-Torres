"""Two transparent strategy alternatives, separate from the three financial scenarios."""
import json
from .consultant import industry

CLASSIFICATION = "DETERMINISTIC_FROM_UNVERIFIED_INPUTS_NOT_LIVE_AI"


def recommendations(facts):
    description = " ".join(str(facts.get(k, "")) for k in ("concept", "industry", "goals", "preferences"))
    cleaning = industry(description) == "cleaning"
    commercial = any(x in description.lower() for x in ("commercial", "office", "contract"))
    preferred = "contract_first" if commercial and facts["budget_cents"] >= 500000 else "focused_launch"
    options = [
        {"key": "focused_launch", "name": "Focused recurring-client launch" if cleaning else "Focused customer-validation launch",
         "approach": "Start owner-operated with a narrow recurring cleaning offer and validate demand before expanding." if cleaning
                     else "Validate one customer segment and a narrow offer before adding capacity.",
         "target": "Repeat local cleaning clients" if cleaning else "One clearly defined initial customer segment",
         "advantages": ["Lower initial staffing commitments", "Validate demand before expanding", "Repeat customers can improve cash-flow predictability"],
         "disadvantages": ["Owner capacity limits growth", "Customer demand and retention are unverified", "Insurance and local requirements still need review"],
         "validation": "Validate demand and pricing for the focused offer with prospective customers before spending."},
        {"key": "contract_first", "name": "Contract-led commercial launch" if cleaning else "Contract-led partnership launch",
         "approach": "Seek a small commercial cleaning contract before committing to equipment or staffing." if cleaning
                     else "Seek prospective customer or partner commitments before adding delivery capacity.",
         "target": "Small commercial cleaning customers" if cleaning else "Prospective contract customers or delivery partners",
         "advantages": ["Potentially larger repeat engagements", "Capacity can follow confirmed customer needs", "Clearer scope through written agreements"],
         "disadvantages": ["Longer sales and collection cycles", "May require more insurance, equipment or staffing", "Contract interest is not guaranteed demand"],
         "validation": "Validate prospective contract scope, payment terms and capacity needs before committing money."},
    ]
    for option in options:
        option.update(preferred=option["key"] == preferred, classification=CLASSIFICATION,
                      reason=("B.I.G. prefers a narrower launch to limit unverified commitments at the stated budget."
                              if preferred == "focused_launch" else
                              "B.I.G. prefers contract-led validation because commercial intent and a larger stated budget are present."),
                      jurisdiction=facts["jurisdiction"], budget_cents=facts["budget_cents"])
    return options


def selection(facts):
    return facts.get("_strategy")


def source(facts):
    return facts.get("_source")


def initialize_roadmap(db, user, project):
    """Additive only: use the existing shared action/receipt and Mission Control stores."""
    from . import business_orchestrator as engine
    from ..models import ExecutionTask
    plan = json.loads(project.plan_json)
    strategy = plan.get("business_strategy")
    if not strategy or engine.rows(db, project):
        return
    for key, (title, subsystem, deps) in engine.SPECS.items():
        a, r = engine.create_action(db, user, project, key, title, subsystem, deps)
        engine.evidence(db, user, project, a, "created", "Roadmap automatically prepared from the customer's saved decisions")
        if key == "strategy":
            engine.set_state(a, r, "COMPLETED_VERIFIED")
            engine.evidence(db, user, project, a, "selected_plan_review",
                            "Customer selected business strategy and financial plan, then requested this project",
                            {"strategy_key": strategy["key"], "plan_key": plan["key"]})
    for kpi, task in [
        ("unified:strategy", f"{strategy['validation']} Context: {project.name}; {strategy['jurisdiction']}."),
        ("unified:funding", f"Review {plan['name']} funding gap ${plan['funding_gap_cents']/100:,.2f} against "
         f"the ${project.budget_cents/100:,.2f} budget. Completion records review only, not funding or spending authorization."),
    ]:
        db.add(ExecutionTask(tenant_id=user.tenant_id, business_id=project.business_id,
                            horizon="today", task=task, budget="0", status="todo", kpi=kpi))
    db.flush()
    engine.reconcile(db, user, project)
