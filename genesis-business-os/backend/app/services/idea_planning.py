"""No-network, deterministic planning estimates using the existing financial engine."""
from decimal import Decimal, ROUND_HALF_UP

from .consultant import TEMPLATES, financial_model, industry


def cents(dollars):
    return int((Decimal(str(dollars)) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def itemize(total, labels, percentages):
    values = [total * p // 100 for p in percentages]
    values[-1] += total - sum(values)
    return [{"label": label, "amount_cents": value} for label, value in zip(labels, values)]


def prepare_plans(facts):
    description = facts["industry"] + " " + facts["concept"]
    # Normalize common food synonyms before reusing the existing template classifier.
    kind = industry(description + (" food" if any(w in description.lower() for w in ("bakery", "baking")) else ""))
    margin, floor, fixed, ticket = TEMPLATES[kind]
    available = facts["budget_cents"]
    requirements = [
        {"title": "Choose structure and check registration / assumed-name requirements",
         "status": "NEEDS_VERIFICATION", "reason": "Depends on structure, name and county; no filing has occurred.",
         "official_url": "https://www.sba.gov/business-guide/launch-your-business/register-your-business"},
        {"title": "Check state and local licenses, permits, zoning and service-tax treatment",
         "status": "NEEDS_VERIFICATION", "reason": f"Confirm for {facts['jurisdiction']}, municipality and actual activities.",
         "official_url": "https://www.sba.gov/business-guide/launch-your-business/apply-licenses-permits"},
        {"title": "Review federal tax registration and recordkeeping",
         "status": "CONDITIONALLY_REQUIRED", "reason": "Entity, ownership and employees determine obligations. Ask a qualified tax professional.",
         "official_url": "https://www.irs.gov/businesses/small-businesses-self-employed/starting-a-business"},
        {"title": "Review insurance, worker safety and employment obligations",
         "status": "NEEDS_VERIFICATION", "reason": "Staffing, contracts, vehicles and work sites change requirements.",
         "official_url": "https://www.sba.gov/business-guide/launch-your-business/get-business-insurance"},
    ]
    if facts["jurisdiction"] == "NY":
        requirements.append({
            "title": "New York business checklist and local requirements",
            "status": "NEEDS_VERIFICATION",
            "reason": "Use New York Business Express and the relevant locality; industry-specific registration, sales tax and employment treatment require review.",
            "official_url": "https://www.businessexpress.ny.gov/",
        })
    if kind == "cleaning":
        requirements.append({
            "title": "Review cleaning-chemical handling, work-site safety and worker training",
            "status": "NEEDS_VERIFICATION",
            "reason": "Residential versus commercial work, products, staffing and customer sites affect safety responsibilities.",
            "official_url": "https://www.osha.gov/cleaning-industry",
        })
    if kind == "food":
        requirements.append({
            "title": "Review food-business permits, health rules and home-kitchen restrictions",
            "status": "NEEDS_VERIFICATION",
            "reason": "Products, preparation site, sales channels and local health rules affect what is permitted; professional/local agency review is needed.",
            "official_url": "https://www.fda.gov/food/food-industry/how-start-food-business",
        })
    services = [
        {"category": "formation", "reason": "Compare structure and registration support; no formation service is engaged."},
        {"category": "legal", "reason": "Review service contracts, liability and applicable local rules."},
        {"category": "tax", "reason": "Review sales tax, bookkeeping and tax registrations with a qualified professional."},
        {"category": "insurance", "reason": "Request suitable coverage quotes before taking on customer work."},
        {"category": "marketing_growth", "reason": "Prepare a small demand-validation test; no advertisement is published."},
    ]
    plans = []
    configs = [
        ("start_smart", "Start Smart", 65, 25, 12, 1,
         "Owner-operated, tightly scoped service; validate demand before hiring."),
        ("build_strong", "Build Strong", 160, 55, 28, 2,
         "Build repeat customers, stronger equipment and a repeatable operating process."),
        ("grow_big", "Grow Big", 360, 100, 60, 3,
         "Prepare for a small team and wider service area after demand and capital are validated."),
    ]
    for key, name, startup_pct, monthly_pct, units, reserve_months, strategy in configs:
        startup = cents(floor) * startup_pct // 100
        monthly = cents(fixed) * monthly_pct // 100
        reserve = monthly * reserve_months
        revenue = cents(ticket) * units
        twin = {"monthly_revenue": revenue / 100, "monthly_fixed_cost": monthly / 100,
                "gross_margin": margin, "cash": max(0, available - startup) / 100}
        financials = financial_model(twin)
        required = startup + reserve
        plans.append({
            "key": key, "name": name, "strategy": strategy,
            "business_model": f"{kind.title()} service/product sales using assumed ticket pricing.",
            "target_customers": "A locally validated customer segment; confirm needs through interviews.",
            "market_assumptions": ["Demand, competitor prices and conversion have not been researched or verified."],
            "startup_items": itemize(startup,
                ["Equipment / setup allowance", "Initial supplies", "Registration / professional-review allowance",
                 "Insurance / deposits allowance", "Initial marketing test", "Contingency"],
                [40, 15, 10, 15, 10, 10]),
            "monthly_items": itemize(monthly,
                ["Transport / space allowance", "Insurance allowance", "Software / administration",
                 "Marketing allowance", "Other fixed overhead"], [25, 20, 10, 25, 20]),
            "startup_total_cents": startup, "monthly_fixed_cents": monthly,
            "reserve_cents": reserve, "funding_required_cents": required,
            "available_budget_cents": available, "funding_gap_cents": max(0, required - available),
            "average_ticket_cents": cents(ticket), "monthly_units": units, "gross_margin": margin,
            "monthly_revenue_cents": revenue,
            "operating_profit_cents": cents(financials["operating_profit"]),
            "break_even_revenue_cents": cents(financials["break_even_revenue"]),
            "revenue_scenarios": [
                {"label": label, "revenue_cents": revenue * pct // 100,
                 "operating_profit_cents": cents(financial_model({
                     **twin, "monthly_revenue": revenue * pct / 10000,
                 })["operating_profit"])}
                for label, pct in (("Lower demand (60%)", 60), ("Base assumption", 100), ("Higher demand (130%)", 130))
            ],
            "assumptions": [
                "All prices and quantities are unverified template estimates, not quotes or AI output.",
                f"Assumes {units} sales/month at ${ticket:g} each; capacity and demand require validation.",
                f"Assumes {margin:.0%} gross margin; variable delivery costs are deducted before fixed expenses.",
                f"Funding includes startup plus {reserve_months} month(s) of fixed-cost reserve; variable-cost timing may require extra cash.",
                "Owner compensation, income taxes, debt service and jurisdiction-specific fees are excluded.",
                "Fixed overhead and startup allowances must be replaced with actual local quotes.",
                "Customer goals, preferences and notes are preserved but not interpreted by a live AI model.",
            ],
            "risks": ["Demand may not materialize.", "Costs, taxes and permit requirements may exceed allowances.",
                      "Hiring and expansion require separate operational and professional review."],
            "marketing": "Interview potential customers, test a narrow offer and track conversion before scaling.",
            "milestones": ["Validate demand and local obligations", "Get supplier and insurance quotes",
                           "Review the funding gap", "Authorize only separately reviewed launch actions"],
            "requirements": requirements, "service_needs": services,
            "classification": "SYSTEM_CALCULATED_FROM_UNVERIFIED_ESTIMATES",
            "recommended": False, "recommendation_reason": "",
        })
    recommended = next((p for p in plans if not p["funding_gap_cents"]), plans[0])
    recommended["recommended"] = True
    recommended["recommendation_reason"] = (
        "Lowest-capital option within the stated budget; validate demand and assumptions first."
        if not recommended["funding_gap_cents"] else
        "Lowest-capital option, but still has a funding gap. Reduce scope or confirm additional funding before spending."
    )
    return plans
