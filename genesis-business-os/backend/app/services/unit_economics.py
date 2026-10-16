"""Reproducible RESEARCH MODEL only. Never changes billing, providers or customer prices.

USD rates: official pages accessed 2026-10-16 UTC. Usage/support/CAC assumptions
are simulations, NOT production measurements or evidence of model quality.
Run: python -m app.services.unit_economics
"""
import json
from decimal import Decimal, ROUND_FLOOR

D = Decimal
CONFIGURATIONS = {
    "economy": {"provider":"OpenAI", "model":"gpt-6-luna", "input":"0.10", "cached":"0.01",
                "output":"0.50", "cache_write":"0.125", "source":"https://developers.openai.com/api/docs/pricing"},
    "balanced": {"provider":"Google", "model":"gemini-3.1-flash-lite", "input":"0.25", "cached":"0.025",
                 "output":"1.50", "cache_write":None, "source":"https://ai.google.dev/gemini-api/docs/pricing"},
    "advanced": {"provider":"Anthropic", "model":"claude-opus-5-5", "input":"4.00", "cached":"0.20",
                 "output":"20.00", "cache_write":"5.00", "source":"https://platform.claude.com/docs/en/about-claude/pricing"},
}
PRICES = {"discover":D("0"), "start":D("9.99"), "build":D("19.99"), "operate":D("39.99")}
USAGE = {"light":(2,D(".5")), "typical":(10,D("3")), "heavy":(100,D("12")), "extreme":(2000,D("60"))}


def workflow_cost(configuration, *, input_tokens=15000, output_tokens=5000,
                  cached_fraction=D(".25"), attempts=D("1.2"), success_rate=D(".95"),
                  tool_cost=D(".01"), document_compute=D(".005")):
    if (input_tokens < 0 or output_tokens < 0 or not D(0) <= cached_fraction <= D(1)
        or attempts < 1 or not D(0) < success_rate <= 1 or tool_cost < 0 or document_compute < 0):
        raise ValueError("Invalid simulated cost assumptions")
    rates = CONFIGURATIONS[configuration]
    tokens = (D(input_tokens)*(1-cached_fraction)*D(rates["input"])
              + D(input_tokens)*cached_fraction*D(rates["cached"])
              + D(output_tokens)*D(rates["output"]))/D(1000000)
    # Upper-bound simulation assumes complete billable attempts even when failed.
    # Conservative: re-create the cached portion once per attempt. Google creation
    # uses the normal input rate plus one hour's published $1/M-token storage.
    creation = D(input_tokens)*cached_fraction*D(rates["cache_write"] or rates["input"])/D(1000000)
    storage = D(input_tokens)*cached_fraction/D(1000000) if configuration == "balanced" else D(0)
    inference = (tokens+creation+storage) * attempts / success_rate
    return {"inference":inference, "cache_creation":creation, "cache_storage_one_hour":storage,
            "tools":tool_cost, "documents":document_compute,
            "total":inference+tool_cost+document_compute}


def customer_cost(tier, usage, configuration):
    price = PRICES[tier]; count, support_minutes = USAGE[usage]
    count = 0 if tier == "discover" else count
    work = workflow_cost(configuration)
    ai = count*work["inference"]; tools = count*work["tools"]; documents = count*work["documents"]
    processor = price*D(".029")+D(".30") if price else D(0)
    billing = price*D(".007")
    refunds = price*D(".02")
    disputes = price*D(".005")+D(".015") if price else D(0)
    support = support_minutes*D(".50")  # $30/hour fully-variable support assumption
    infrastructure = D(".20")
    variable = ai+tools+documents+processor+billing+refunds+disputes+support+infrastructure
    contribution = price-variable
    fixed = D("50")/D("100")  # $50/month fixed opex / 100 active customers
    cac = D("30")/D("6")     # $30 CAC allocated across 6 paid months, not a measured lifetime
    allowance = max(D(0),(price-(variable-ai-tools-documents))/work["total"])
    return {"tier":tier, "usage":usage, "configuration":configuration, "workflows":count,
            "gross_revenue":price, "ai_inference":ai, "tool_execution":tools,
            "document_processing":documents, "processing":processor, "billing":billing,
            "refund_reserve":refunds, "dispute_reserve":disputes, "variable_support":support,
            "variable_infrastructure":infrastructure, "variable_delivery_cost":variable,
            "contribution_margin":contribution, "allocated_fixed_opex":fixed,
            "allocated_customer_acquisition_cost":cac,
            "estimated_operating_profit_before_tax":contribution-fixed-cac,
            "break_even_workflows_before_fixed_and_cac":int(allowance.to_integral_value(rounding=ROUND_FLOOR)),
            "unsustainable":contribution < 0,
            "actual_measured_ai_cost":None, "actual_external_spending":0}


def report():
    def serial(value):
        if isinstance(value,D):
            return str(value.quantize(D(".000001")))
        if isinstance(value,dict):return {k:serial(v) for k,v in value.items()}
        if isinstance(value,list):return [serial(v) for v in value]
        return value
    return serial({"classification":"RESEARCHED_ONLY_SIMULATED_NOT_COMMERCIAL_AUTHORIZATION",
        "access_date_utc":"2026-10-16", "configurations":CONFIGURATIONS,
        "workflow_costs":{k:workflow_cost(k) for k in CONFIGURATIONS},
        "assumptions":{"input_tokens":15000,"output_tokens":5000,"cached_input_fraction":".25",
          "attempts_per_workflow":"1.2","success_rate":".95","fixed_opex_monthly_usd":"50",
          "active_customers":100,"cac_per_customer_usd":"30","cac_allocation_months":6},
        "scenarios":[customer_cost(t,u,c) for t in PRICES for u in USAGE for c in CONFIGURATIONS]})


if __name__ == "__main__":
    print(json.dumps(report(),indent=2))
