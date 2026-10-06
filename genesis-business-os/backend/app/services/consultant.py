from typing import Any
import hashlib, json
TEMPLATES={"consulting":(.72,1500,1800,1500),"cleaning":(.48,2500,2200,220),"ecommerce":(.42,4000,2500,85),"food":(.32,15000,8500,24),"software":(.82,6000,5000,99),"transportation":(.38,12000,6500,450),"general":(.50,3000,3000,250)}
def industry(s):
 s=s.lower()
 for k,ws in {"cleaning":["clean","janitorial"],"ecommerce":["ecommerce","online store","shopify"],"food":["restaurant","food","catering"],"software":["software","saas","app"],"transportation":["truck","delivery","transport"],"consulting":["consult","agency"]}.items():
  if any(w in s for w in ws): return k
 return "general"
def generate_candidates(objective:str,constraints:dict[str,Any]):
 k=industry(objective+" "+json.dumps(constraints)); gm,floor,fixed,ticket=TEMPLATES[k]; cap=float(constraints.get("capital",constraints.get("budget",10000)) or 10000); hrs=float(constraints.get("hours_per_week",40) or 40); out=[]
 for name,spend,capacity in [("Lean Validation",.55,.7),("Balanced Launch",1,1),("Growth Launch",1.45,1.3)]:
  startup=round(max(floor,min(cap*.72,floor*spend)),2); units=max(1,round(hrs*4.33*capacity/2)); revenue=round(ticket*units,2); op=round(revenue*gm-fixed*spend,2)
  out.append({"name":name,"industry":k,"startup_budget":startup,"monthly_fixed_cost":round(fixed*spend,2),"average_ticket":ticket,"estimated_monthly_units":units,"estimated_monthly_revenue":revenue,"gross_margin":gm,"estimated_operating_profit":op,"break_even_revenue":round(fixed*spend/max(gm,.01),2),"feasible":startup<=cap,"assumptions":["Planning economics are assumptions until verified.","Taxes, debt service and owner compensation are excluded unless supplied."]})
 return out
def financial_model(t):
 rev=float(t.get("monthly_revenue",t.get("estimated_monthly_revenue",0)) or 0); gm=float(t.get("gross_margin",.5) or .5); fixed=float(t.get("monthly_fixed_cost",3000) or 0); cash=float(t.get("cash",t.get("starting_cash",10000)) or 0); op=rev*gm-fixed; burn=max(0,-op)
 return {"monthly_revenue":round(rev,2),"gross_profit":round(rev*gm,2),"operating_profit":round(op,2),"break_even_revenue":round(fixed/max(gm,.01),2),"cash":round(cash,2),"monthly_burn":round(burn,2),"runway_months":None if burn==0 else round(cash/burn,1)}
def stress_test(t):
 f=financial_model(t); rev=f["monthly_revenue"]; fixed=float(t.get("monthly_fixed_cost",3000) or 0); gm=float(t.get("gross_margin",.5) or .5); cases=[("Revenue -40%",rev*.6,gm,fixed),("Gross margin -20%",rev,max(.05,gm*.8),fixed),("Fixed costs +25%",rev,gm,fixed*1.25),("Revenue -25% + costs +15%",rev*.75,gm,fixed*1.15)]
 return [{"scenario":n,"operating_profit":round(r*g-x,2),"survives_operating_break_even":r*g-x>=0} for n,r,g,x in cases]
def executive_board(question,twin,evidence):
 f=financial_model(twin); st=stress_test(twin); verified=sum(e.get("classification") in ("verified","actual") for e in evidence); assumed=sum(e.get("classification")=="ai_assumption" for e in evidence); conf=max(25,min(90,55+verified*6-assumed*4))
 agents={"CEO":{"position":"Proceed in stages" if f["operating_profit"]>=0 else "Validate before scaling","reason":"Preserve strategic options while testing the objective."},"CFO":{"position":"Financially supportable" if f["operating_profit"]>=0 else "Cash-risk flagged","reason":f'Operating profit ${f["operating_profit"]:,.2f}; break-even ${f["break_even_revenue"]:,.2f}.'},"CMO":{"position":"Demand validation required","reason":"Use capped tests before large acquisition commitments."},"COO":{"position":"Capacity gate required","reason":"Scale only after fulfillment capacity is measurable."},"Risk":{"position":"Downside controls required","reason":f'{sum(not x["survives_operating_break_even"] for x in st)} of {len(st)} modeled shocks fall below operating break-even.'},"Cyber":{"position":"Least privilege / approval gate","reason":"Sensitive exports, writes and financial actions require independent authorization."}}
 conflicts=[]
 if f["operating_profit"]<0: conflicts.append("Growth spending conflicts with operating break-even.")
 if any(not x["survives_operating_break_even"] for x in st): conflicts.append("Growth conflicts with downside cash-preservation requirements under modeled shocks.")
 return {"question":question,"confidence":conf,"financials":f,"agents":agents,"conflicts":conflicts,"recommended_path":["Verify highest-impact assumptions.","Run a capped validation test.","Recalculate unit economics from actual results.","Scale only after threshold and authorization checks."],"stress_tests":st,"evidence_count":len(evidence)}
def decision_hash(p): return hashlib.sha256(json.dumps(p,sort_keys=True,default=str).encode()).hexdigest()
