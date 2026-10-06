
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
import uuid

@dataclass
class FounderReality:
    cash: float
    reserve_floor: float
    hours_per_week: float
    skills: List[str]
    assets: List[str]
    location: str = ""

@dataclass
class DestinationContract:
    target_monthly_owner_income: float
    horizon_months: int
    max_risk_cash: float

@dataclass
class Checkpoint:
    id: str
    title: str
    proof_required: List[str]
    max_cash_commitment: float
    status: str = "LOCKED"

class GenesisRouteEngine:
    """
    Reference engine for:
    Reality -> Destination -> Candidate Routes -> Next Turn -> Proof -> Outcome -> Reroute.
    Critical arithmetic is deterministic. AI may explain/propose but does not override policy.
    """
    def spendable(self, reality: FounderReality, dest: DestinationContract) -> float:
        return max(0.0, min(dest.max_risk_cash, reality.cash - reality.reserve_floor))

    def counterfactual_requirements(self, dest: DestinationContract, avg_ticket: float,
                                    gross_margin: float, close_rate: float) -> Dict[str, float]:
        if min(avg_ticket, gross_margin, close_rate) <= 0:
            raise ValueError("Inputs must be positive.")
        revenue_needed = dest.target_monthly_owner_income / gross_margin
        customers = revenue_needed / avg_ticket
        qualified_opportunities = customers / close_rate
        return {
            "monthly_revenue_needed": round(revenue_needed, 2),
            "customers_needed": round(customers, 1),
            "qualified_opportunities_needed": round(qualified_opportunities, 1),
        }

    def route_portfolio(self, reality: FounderReality, dest: DestinationContract) -> List[Dict[str, Any]]:
        budget = self.spendable(reality, dest)
        base = [
          ("Validate-first service route", 0.20, "LOW", "Fastest evidence with minimal fixed cost"),
          ("Lean local route", 0.45, "MEDIUM", "Adds small tools/outreach after demand signal"),
          ("Build-before-sell route", 0.85, "HIGH", "Higher upfront commitment; requires stronger proof"),
        ]
        routes=[]
        for name, fraction, risk, reason in base:
            routes.append({
              "route_id": str(uuid.uuid4()),
              "name": name,
              "initial_cash_envelope": round(budget*fraction,2),
              "risk": risk,
              "reason": reason
            })
        return routes

    def checkpoints(self, reality: FounderReality, dest: DestinationContract) -> List[Checkpoint]:
        budget=self.spendable(reality,dest)
        return [
          Checkpoint("P1","Demand proof",["3 customer conversations","1 explicit buying signal"],round(budget*.20,2),"ACTIVE"),
          Checkpoint("P2","Revenue proof",["first paid transaction","actual cost recorded"],round(budget*.45,2)),
          Checkpoint("P3","Repeatability proof",["3 paid transactions","delivery time measured","margin measured"],round(budget*.65,2)),
          Checkpoint("P4","Scale proof",["repeatable acquisition signal","capacity check","cash buffer intact"],round(budget,2)),
        ]

    def next_turn(self, reality: FounderReality, dest: DestinationContract, proofs: Dict[str,bool]) -> Dict[str,Any]:
        cps=self.checkpoints(reality,dest)
        for cp in cps:
            if not all(proofs.get(x,False) for x in cp.proof_required):
                return {
                  "checkpoint": cp.title,
                  "action": f"Complete evidence for {cp.title.lower()}",
                  "proof_missing": [x for x in cp.proof_required if not proofs.get(x,False)],
                  "max_cash_commitment": cp.max_cash_commitment,
                  "why": "Genesis advances only when the current route has enough real-world evidence."
                }
        return {"checkpoint":"Route complete","action":"Generate next growth route","proof_missing":[],"max_cash_commitment":self.spendable(reality,dest)}

    def reroute(self, old: FounderReality, new: FounderReality, dest: DestinationContract) -> Dict[str,Any]:
        changed=[]
        for k in ("cash","reserve_floor","hours_per_week","skills","assets","location"):
            if getattr(old,k)!=getattr(new,k): changed.append(k)
        affected=set()
        mapping={
          "cash":{"resource_envelope","route_feasibility","next_turn"},
          "reserve_floor":{"resource_envelope","route_feasibility","next_turn"},
          "hours_per_week":{"capacity","timeline","route_feasibility","next_turn"},
          "skills":{"route_feasibility","execution_plan"},
          "assets":{"route_feasibility","startup_costs","execution_plan"},
          "location":{"requirements","filings","tax_assumptions","operating_costs","route_feasibility"},
        }
        for c in changed: affected |= mapping[c]
        return {
          "changed": changed,
          "invalidate_and_recompute": sorted(affected),
          "preserve_unaffected": True,
          "new_spendable_envelope": self.spendable(new,dest),
          "authorization_recheck_required": bool({"cash","reserve_floor","location"} & set(changed))
        }

    def evolution(self, reality: FounderReality, dest: DestinationContract, metrics: Dict[str, float]) -> Dict[str, Any]:
        """Deterministic Business Evolution Engine.
        Compares a small set of possible futures without pretending estimates are guarantees.
        It returns one recommended evolution so the consumer UI stays simple.
        """
        revenue=max(0.0,float(metrics.get('monthly_revenue',0) or 0))
        repeat_share=min(1.0,max(0.0,float(metrics.get('repeat_customer_share',0) or 0)))
        gross_margin=min(1.0,max(0.0,float(metrics.get('gross_margin',0.5) or 0.5)))
        capacity=min(1.0,max(0.0,float(metrics.get('capacity_used',0.5) or 0.5)))
        spendable=self.spendable(reality,dest)
        futures=[]
        def add(key,title,score,cost,why,action):
            futures.append({'key':key,'title':title,'score':round(max(0,min(100,score)),1),'estimated_cash_needed':round(max(0,cost),2),'why':why,'next_action':action})
        gap=max(0.0,dest.target_monthly_owner_income-revenue)
        add('validate','Validate demand deeper',82 if revenue<=0 else 45,spendable*.10,'Protect cash until customers prove demand.','Get one more verified buying signal before expanding.')
        add('repeat','Strengthen repeat customers',45+repeat_share*45+(10 if revenue>0 else 0),spendable*.15,'Repeat demand can improve predictability without forcing a large expansion.','Create and test one simple repeat-customer offer.')
        add('price','Test pricing',50+(15 if gross_margin<.55 else 5),0,'A controlled price test can improve margin without adding fixed cost.','Test one price or package change with qualified customers.')
        add('acquire','Increase customer acquisition',35+(20 if revenue>0 and gross_margin>=.45 else 0)+(10 if capacity<.8 else -20),spendable*.25,'Acquisition is strongest after demand and delivery capacity are visible.','Run one measurable customer-acquisition test inside the resource envelope.')
        add('capacity','Increase capacity',25+(45 if capacity>=.8 and revenue>0 else 0),spendable*.35,'Capacity should expand only when real demand is pressing against current limits.','Measure the current bottleneck before adding labor, tools, or overhead.')
        futures.sort(key=lambda x:x['score'],reverse=True)
        best=futures[0]
        generation='GEN 1 · Validate' if revenue<=0 else ('GEN 2 · Stabilize' if revenue < dest.target_monthly_owner_income*.5 else ('GEN 3 · Multiply' if gap>0 else 'GEN 4 · Expand'))
        return {
            'generation':generation,
            'destination_monthly_income':round(dest.target_monthly_owner_income,2),
            'current_monthly_revenue':round(revenue,2),
            'recommended_evolution':best,
            'possible_futures':futures[:4],
            'business_dna':{
                'repeat_customer_signal':'STRONG' if repeat_share>=.4 else ('EMERGING' if repeat_share>0 else 'UNKNOWN'),
                'margin_signal':'HEALTHY' if gross_margin>=.5 else 'WATCH',
                'capacity_signal':'TIGHT' if capacity>=.8 else 'AVAILABLE',
                'cash_rule':f'Keep recommendations within ${spendable:.2f} spendable risk capital.'
            },
            'disclaimer':'Possible futures are decision support based on supplied and verified business data; they are not guaranteed outcomes.'
        }
