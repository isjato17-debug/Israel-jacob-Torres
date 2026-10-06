from __future__ import annotations
from typing import Any
from datetime import datetime, timezone
import math, uuid

def uid(): return str(uuid.uuid4())
def founder_score(profile:dict[str,Any])->dict[str,Any]:
    capital=float(profile.get("capital",0) or 0); hours=float(profile.get("hours_per_week",0) or 0)
    experience=float(profile.get("experience_years",0) or 0); risk=float(profile.get("risk_tolerance",5) or 5)
    readiness=min(100,round((min(capital,50000)/50000)*25+(min(hours,60)/60)*30+(min(experience,10)/10)*25+(risk/10)*20))
    return {"readiness":readiness,"capital_band":"micro" if capital<5000 else "small" if capital<25000 else "growth",
            "time_band":"part-time" if hours<30 else "full-time","risk_band":"low" if risk<=3 else "moderate" if risk<=7 else "high"}

def battle_mode(twin:dict[str,Any])->list[dict[str,Any]]:
    rev=float(twin.get("monthly_revenue",0) or 0); gm=float(twin.get("gross_margin",.5) or .5); fixed=float(twin.get("monthly_fixed_cost",3000) or 0)
    cases=[("Defensive",.85,.98,.85),("Base",1,1,1),("Growth",1.25,.96,1.20)]
    return [{"scenario":n,"revenue":round(rev*r,2),"gross_margin":round(gm*m,3),"fixed_cost":round(fixed*f,2),
             "operating_profit":round(rev*r*gm*m-fixed*f,2)} for n,r,m,f in cases]

def failure_lab(twin:dict[str,Any])->list[dict[str,Any]]:
    rev=float(twin.get("monthly_revenue",0) or 0); gm=float(twin.get("gross_margin",.5) or .5); fixed=float(twin.get("monthly_fixed_cost",3000) or 0); cash=float(twin.get("cash",10000) or 0)
    scenarios=[("Revenue collapse",.60,gm,fixed),("Ad cost shock",1,gm,fixed+float(twin.get("ad_spend",0) or 0)),("Supplier +25%",1,max(.05,gm*.85),fixed),
               ("Major customer lost",.70,gm,fixed),("Fixed costs +25%",1,gm,fixed*1.25),("Combined downside",.55,max(.05,gm*.8),fixed*1.2)]
    out=[]
    for n,r,g,f in scenarios:
        op=rev*r*g-f; burn=max(0,-op); runway=None if burn==0 else round(cash/burn,1)
        out.append({"scenario":n,"operating_profit":round(op,2),"monthly_burn":round(burn,2),"runway_months":runway,"survives":op>=0,
                    "response":"Preserve cash, reduce reversible spend, validate demand, renegotiate commitments." if op<0 else "Maintain reserves and monitor leading indicators."})
    return out

def execution_plan(goal:str,budget:float=0)->list[dict[str,Any]]:
    tasks=[
      ("today","Define measurable customer/problem hypothesis",0),
      ("today","List three assumptions that could invalidate the plan",0),
      ("week","Interview or test with first prospective customers",min(budget*.05,250)),
      ("week","Create offer, price and acquisition test",min(budget*.10,500)),
      ("month","Measure conversion, CAC, margin and delivery capacity",min(budget*.15,1000)),
      ("90days","Scale only the validated channel and preserve reserve",min(budget*.30,3000)),
    ]
    return [{"id":uid(),"horizon":h,"task":t,"budget":round(b,2),"status":"todo","kpi":"completed/validated"} for h,t,b in tasks]

def variance_report(twin:dict[str,Any],actuals:list[dict[str,Any]])->list[dict[str,Any]]:
    out=[]
    for a in actuals:
        k=a["key"]; forecast=twin.get(k); actual=float(a["value"])
        try:
            fv=float(forecast); delta=actual-fv; pct=None if fv==0 else delta/fv*100
            out.append({"key":k,"forecast":fv,"actual":actual,"variance":round(delta,2),"variance_pct":None if pct is None else round(pct,1),
                        "material":abs(pct or 0)>=10})
        except (TypeError, ValueError): out.append({"key":k,"forecast":forecast,"actual":actual,"variance":None,"variance_pct":None,"material":False,"forecast_valid":False})
    return out
