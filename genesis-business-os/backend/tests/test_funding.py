import hashlib
import json
from datetime import datetime, timezone
import pytest
from app.services.funding import LoanQuote, affordability
from app.services.funding_catalog import match
from test_unified_intelligence import env, PASSWORD
from test_project_execution import create
from test_autoform import PASS
from test_big_consultation import account

PROFILE = {"expected_version":0,"consent":True,"circumstance":"visa_holder","work_authorization":"uncertain",
    "adult":True,"us_resident":True,"all_owners_us_citizens_or_nationals":False,
    "women_owned_50_percent":True,"amount_cents":300000,
    "use_of_funds":"Initial supplies, insurance quotes and working capital for the saved cleaning plan."}

@pytest.fixture(autouse=True)
def fixed_fresh_source_fixture(monkeypatch):
    # Acceptance fixture only; production snapshots must never auto-refresh dates.
    monkeypatch.setattr("app.services.funding_catalog.CHECKED",datetime.now(timezone.utc).date().isoformat())


def test_stale_sources_explicitly_require_reverification(monkeypatch):
    monkeypatch.setattr("app.services.funding_catalog.CHECKED","2020-01-01")
    assert all(v["match_status"] == "SOURCE_STALE_REVERIFY_REQUIRED"
               for v in match(PROFILE,"NY") if v["kind"] != "DIRECTORY")


def saved(env):
    c,h,user,_,_=env
    p,o,docs=create(env)
    assert c.put(docs+"/passport",headers=h,json={"expected_version":0,"consent":True,"fields":PASS}).status_code==200
    root=f"/api/v2/projects/{p['id']}/funding"
    r=c.put(root+"/profile",headers=h,json=PROFILE)
    assert r.status_code==200,r.text
    return p,root,r.json(),o


@pytest.mark.parametrize("circumstance",["visa_holder","permanent_resident"])
def test_immigrant_journey_screening_draft_exact_approval_and_no_submission(env,circumstance):
    c,h,user,_,_=env
    p,root,view,o=saved(env)
    view=c.put(root+"/profile",headers=h,json={**PROFILE,"expected_version":view["version"],
        "circumstance":circumstance}).json()
    matches={x["id"]:x for x in view["opportunities"]}
    assert matches["sba_microloan"]["match_status"]=="INELIGIBLE_PUBLISHED_CRITERION"
    assert matches["kiva_us"]["match_status"]=="POTENTIAL_MATCH_NOT_VERIFIED"
    assert matches["amber_grant"]["match_status"]=="POTENTIAL_MATCH_NOT_VERIFIED"
    assert matches["federal_grants"]["match_status"]=="DISCOVERY_DIRECTORY_NOT_AWARD"
    assert len(view["applications"])==2
    packet=next(a for a in view["applications"] if a["opportunity_id"]=="kiva_us")
    assert packet["packet"]["business_name"]==PASS["business_name"]
    assert "circumstance" not in json.dumps(packet["packet"])
    assert c.post(root+f"/applications/{packet['id']}/approve",headers=h,json={
        "revision":packet["revision"],"content_hash":"0"*64,"confirmed":True}).status_code==409
    response=c.post(root+f"/applications/{packet['id']}/approve",headers=h,json={
        "revision":packet["revision"],"content_hash":packet["content_hash"],"confirmed":True})
    assert response.status_code==200,response.text
    assert next(a for a in response.json()["applications"] if a["id"]==packet["id"])["approval_status"]=="APPROVED_INTERNAL_PREPARATION_ONLY"
    download=c.get(root+f"/applications/{packet['id']}/download")
    assert hashlib.sha256(download.content).hexdigest()==packet["content_hash"]
    assert all(a["submission_status"]=="BLOCKED_NO_APPROVED_INTEGRATION" for a in view["applications"])
    status=c.get(o).json()
    assert status["signatures"]==status["submissions"]==[]
    assert any(a["key"]=="funding:kiva_us" and a["status"]=="COMPLETED_VERIFIED" for a in status["actions"])
    assert c.post("/api/auth/logout",headers=h).status_code==200
    assert c.get(root).status_code==401
    assert c.post("/api/auth/login",json={"email":user["email"],"password":PASSWORD}).status_code==200
    resumed=c.get(root).json()
    assert {a["id"] for a in resumed["applications"]}=={a["id"] for a in view["applications"]}
    assert resumed["profile"]["circumstance"]==circumstance


def test_corrected_packet_immutable_approval_never_transfers_and_repeat_resume_no_duplicates(env):
    c,h,_,_,_=env
    p,root,view,o=saved(env)
    first=view["applications"][0]
    r=c.post(root+f"/applications/{first['id']}/approve",headers=h,json={
        "revision":first["revision"],"content_hash":first["content_hash"],"confirmed":True})
    assert r.status_code==200
    revised=c.put(root+"/profile",headers=h,json={**PROFILE,"expected_version":view["version"],
        "amount_cents":400000}).json()
    latest=next(a for a in revised["applications"] if a["opportunity_id"]==first["opportunity_id"])
    assert latest["revision"]==2 and latest["approval_status"]=="NEEDS_REVIEW"
    from app.db import SessionLocal
    from app.models import ExecutionTask
    from sqlalchemy import select
    with SessionLocal() as db:
        assert all(t.status == "todo" for t in db.scalars(select(ExecutionTask).where(
            ExecutionTask.business_id == p["business_id"],
            ExecutionTask.task.like("Review internal funding packet:%"))))
    assert c.get(root+f"/applications/{first['id']}/download").content==json.dumps(first["packet"],sort_keys=True,separators=(",",":"),ensure_ascii=False).encode()
    for _ in range(2):
        assert c.post(o+"/run",headers=h,json={}).status_code==200
    assert len(c.get(root).json()["applications"])==4
    assert c.post(root+f"/applications/{first['id']}/approve",headers=h,json={
        "revision":first["revision"],"content_hash":first["content_hash"],"confirmed":True}).status_code==409


def test_missing_passport_once_resume_and_sensitive_scope(env):
    c,h,user,_,_=env
    p,o,docs=create(env);root=f"/api/v2/projects/{p['id']}/funding"
    response=c.put(root+"/profile",headers=h,json=PROFILE)
    assert response.status_code==200 and response.json()["applications"]==[]
    assert any(a["key"]=="funding:kiva_us" and a["status"]=="INFORMATION_REQUIRED" for a in c.get(o).json()["actions"])
    assert c.put(docs+"/passport",headers=h,json={"expected_version":0,"consent":True,"fields":PASS}).status_code==200
    assert len(c.get(root).json()["applications"])==2
    for payload in ({"ssn":"do-not-store"},{"passport_number":"do-not-store"},{"consent":False}):
        assert c.put(root+"/profile",headers=h,json={**PROFILE,"expected_version":1,**payload}).status_code==422
    assert c.put(root+"/profile",json=PROFILE).status_code==403
    other,oh,_=account()
    assert other.get(root).status_code==404
    packet=c.get(root).json()["applications"][0]
    assert other.get(root+f"/applications/{packet['id']}/download").status_code==404
    assert other.post(root+f"/applications/{packet['id']}/approve",headers=oh,json={
        "revision":1,"content_hash":packet["content_hash"],"confirmed":True}).status_code==404
    other.close()
    # An older/uninitialized project must not gain a misleading partial roadmap.
    from app.db import SessionLocal
    from app.models import ProjectAction
    from sqlalchemy import delete
    with SessionLocal() as db:
        db.execute(delete(ProjectAction).where(ProjectAction.project_id == p["id"]))
        db.commit()
    assert c.put(root+"/profile",headers=h,json={**PROFILE,"expected_version":1}).status_code==409


def test_uncertain_and_ineligible_without_funding_guarantee():
    values=match({},"NY")
    assert all(v["match_status"]=="UNCERTAIN_REVIEW_REQUIRED" for v in values if v["kind"]!="DIRECTORY")
    values=match({"adult":False,"us_resident":False,"all_owners_us_citizens_or_nationals":False,
                  "women_owned_50_percent":False},"NY")
    assert all(v["match_status"]=="INELIGIBLE_PUBLISHED_CRITERION" for v in values if v["kind"]!="DIRECTORY")
    assert all(v["eligibility_verification"]=="NOT_CERTIFIED" for v in values)
    for state in ("NV","ND"):
        assert next(v for v in match(PROFILE,state) if v["id"]=="kiva_us")["match_status"]=="INELIGIBLE_PUBLISHED_CRITERION"


@pytest.mark.parametrize("rate,term",[(0,36),(1200,12),(5000,360)])
def test_loan_math_exact_payoff_and_no_approval_claim(rate,term):
    result=affordability(LoanQuote(principal_cents=300000,annual_rate_bps=rate,months=term,upfront_fee_cents=100),1000)
    assert result["schedule"][-1]["balance_cents"]==0
    assert sum(r["payment_cents"]-r["interest_cents"] for r in result["schedule"])==300000
    assert result["total_payments_cents"]==sum(r["payment_cents"] for r in result["schedule"])
    assert result["net_proceeds_cents"]==299900
    assert result["affordability"]=="FAILS_PLAN_CASHFLOW"


def test_quotes_and_manual_outcomes_persist_truthfully(env):
    c,h,_,_,_=env
    p,root,view,_=saved(env)
    payload={"principal_cents":300000,"annual_rate_bps":0,"months":36,"upfront_fee_cents":0}
    assert c.post(root+"/affordability",headers=h,json=payload).status_code==200
    assert c.post(root+"/affordability",headers=h,json=payload).status_code==200
    assert len(c.get(root).json()["loan_comparisons"])==1
    packet=view["applications"][0]
    r=c.patch(root+f"/applications/{packet['id']}/tracking",headers=h,json={
        "deadline":"2026-12-01","reported_outcome":"USER_REPORTED_AWARDED"})
    assert r.status_code==200
    row=next(a for a in r.json()["applications"] if a["id"]==packet["id"])
    assert row["outcome_verification"]=="CUSTOMER_REPORTED_NOT_EXTERNALLY_VERIFIED"
    assert row["submission_status"]=="BLOCKED_NO_APPROVED_INTEGRATION"
