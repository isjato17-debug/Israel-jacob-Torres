"""Private eligibility screening and internal packets, using Phase 1 actions and receipts."""
import json
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Literal
from pydantic import Field
from sqlalchemy import select
from ..models import FundingProfile, FundingApplication, BusinessIdea, ExecutionTask, ExecutionReceiptRecord
from .intelligence_contracts import StrictContract
from .document_engine import canonical
from .test_signing import sha
from .funding_catalog import match, IMMIGRATION_SOURCE
from . import business_orchestrator as engine
from ..v2.documents import passport


class FundingInput(StrictContract):
    expected_version: int = Field(ge=0)
    consent: Literal[True]
    circumstance: Literal["citizen_national", "permanent_resident", "visa_holder", "undisclosed"] = "undisclosed"
    work_authorization: Literal["customer_declares_authorized", "not_authorized", "uncertain"] = "uncertain"
    adult: bool | None = None
    us_resident: bool | None = None
    all_owners_us_citizens_or_nationals: bool | None = None
    women_owned_50_percent: bool | None = None
    amount_cents: int = Field(gt=0, le=100_000_000)
    use_of_funds: str = Field(min_length=5, max_length=2000)


class LoanQuote(StrictContract):
    principal_cents: int = Field(gt=0, le=100_000_000)
    annual_rate_bps: int = Field(ge=0, le=10000)
    months: int = Field(ge=1, le=360)
    upfront_fee_cents: int = Field(default=0, ge=0, le=10_000_000)


def affordability(quote, available_cents):
    principal = Decimal(quote.principal_cents)
    rate = Decimal(quote.annual_rate_bps) / Decimal(120000)
    payment = principal / quote.months if not rate else principal * rate / (1 - (1 + rate) ** (-quote.months))
    balance, total = principal, Decimal(0)
    rounded = payment.quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    schedule = []
    for month in range(1, quote.months + 1):
        interest = (balance * rate).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        due = balance + interest if month == quote.months else min(rounded, balance + interest)
        balance -= due - interest; total += due
        schedule.append({"month":month, "payment_cents":int(due), "interest_cents":int(interest),
                         "balance_cents":int(balance)})
    highest = max(row["payment_cents"] for row in schedule)
    return {"classification":"UNVERIFIED_CUSTOMER_QUOTE_DETERMINISTIC_CALCULATION",
            "monthly_payment_cents":int(rounded), "maximum_payment_cents":highest,
            "total_payments_cents":int(total), "total_interest_cents":int(total - principal),
            "total_cost_with_fee_cents":int(total - principal) + quote.upfront_fee_cents,
            "net_proceeds_cents":quote.principal_cents - quote.upfront_fee_cents,
            "estimated_available_cash_cents":available_cents,
            "coverage_ratio":str((Decimal(available_cents) / highest).quantize(Decimal(".01"))) if highest else None,
            "affordability":"FAILS_PLAN_CASHFLOW" if available_cents < highest else "SCENARIO_ONLY_NOT_UNDERWRITTEN",
            "notice":"Plan cashflow excludes owner pay, taxes and other debts. This is not APR, a lender quote or loan approval.",
            "schedule":schedule}


def profile_for(db, p):
    return db.scalar(select(FundingProfile).where(FundingProfile.project_id == p.id,
                     FundingProfile.user_id == p.user_id, FundingProfile.tenant_id == p.tenant_id))


def applications(db, p):
    return db.scalars(select(FundingApplication).where(FundingApplication.project_id == p.id,
        FundingApplication.user_id == p.user_id, FundingApplication.tenant_id == p.tenant_id)
        .order_by(FundingApplication.created_at.desc(), FundingApplication.revision.desc())).all()


def describe_application(a):
    data = json.loads(a.source_json)
    valid = sha(canonical(data).encode()) == a.content_hash
    return {"id":a.id, "opportunity_id":a.opportunity_id, "revision":a.revision,
            "content_hash":a.content_hash, "integrity_verified":valid, "packet":data if valid else None,
            "approval_status":"APPROVED_INTERNAL_PREPARATION_ONLY" if valid and a.approved_hash == a.content_hash else "NEEDS_REVIEW",
            "deadline":a.deadline, "reported_outcome":a.reported_outcome,
            "outcome_verification":"CUSTOMER_REPORTED_NOT_EXTERNALLY_VERIFIED",
            "submission_status":"BLOCKED_NO_APPROVED_INTEGRATION"}


def view(db, p):
    saved = profile_for(db,p)
    profile = json.loads(saved.profile_json) if saved else {}
    facts = json.loads(db.get(BusinessIdea,p.idea_id).facts_json)
    plan = json.loads(p.plan_json)
    quote_node = engine.rows(db,p).get("funding:affordability")
    comparisons = []
    if quote_node:
        receipts = db.scalars(select(ExecutionReceiptRecord).where(
            ExecutionReceiptRecord.action_id == quote_node[1].id,
            ExecutionReceiptRecord.evidence_type == "internal_output")
            .order_by(ExecutionReceiptRecord.created_at.desc()).limit(3))
        for receipt in receipts:
            item = json.loads(receipt.metadata_json)
            if sha(canonical(item["output"]).encode()) == item["content_hash"]:
                comparisons.append(item["output"])
    return {"version":saved.version if saved else 0, "profile":profile, "loan_comparisons":comparisons,
            "funding_gap_cents":plan["funding_gap_cents"], "opportunities":match(profile,facts["jurisdiction"]),
            "applications":[describe_application(a) for a in applications(db,p)],
            "immigration":{"source":IMMIGRATION_SOURCE,
                "ownership":"Owning a business does not itself establish a right to work in it.",
                "work_authorization":"Customer declarations are not immigration-law verification. Visa conditions and actual activities require individualized review.",
                "licensing":"Licensing is separate from ownership, work authorization and funding eligibility.",
                "escalation":"Consult a qualified immigration attorney or accredited representative before relying on a work/immigration conclusion."},
            "restrictions":["No SSN, passport number, immigration documents or credit report is requested.",
                            "No credit checks, application submission, payment or sensitive-document sharing.",
                            "Internal preparation is not an official lender/agency application."]}


def refresh(db, user, p):
    saved = profile_for(db,p)
    if not saved:
        return
    profile = json.loads(saved.profile_json)
    facts = json.loads(db.get(BusinessIdea,p.idea_id).facts_json)
    plan = json.loads(p.plan_json)
    approved_passport = passport(db,p)
    fields = json.loads(approved_passport.fields_json) if approved_passport else {}
    from .project_execution import save_output
    nodes = engine.rows(db,p)
    previous = applications(db,p)
    for opportunity in match(profile, facts["jurisdiction"]):
        if opportunity["kind"] == "DIRECTORY":
            continue
        key = "funding:" + opportunity["id"]
        if key not in nodes:
            nodes[key] = engine.create_action(db,user,p,key,"Prepare " + opportunity["name"] + " internal packet",
                                               "Funding / AutoForm preparation",[])
            review_key = key + ":review"
            nodes[review_key] = engine.create_action(db,user,p,review_key,"Review exact funding packet",
                                                    "Customer approvals",[key])
            db.add(ExecutionTask(tenant_id=p.tenant_id,business_id=p.business_id,horizon="30d",
                task="Review internal funding packet: " + opportunity["name"], budget="0",
                status="todo", kpi="Exact-revision internal preparation approval; not funding received"))
        action, record = nodes[key]
        review_action, review_record = nodes[key + ":review"]
        review_tasks = db.scalars(select(ExecutionTask).where(
            ExecutionTask.business_id == p.business_id, ExecutionTask.tenant_id == user.tenant_id,
            ExecutionTask.task == "Review internal funding packet: " + opportunity["name"])).all()
        if opportunity["match_status"] in ("INELIGIBLE_PUBLISHED_CRITERION","SOURCE_STALE_REVERIFY_REQUIRED"):
            for task in review_tasks:
                task.status = "todo"
            engine.set_state(action,record,"BLOCKED")
            record.result_json = canonical({"reason":opportunity["match_status"] + ": " + "; ".join(opportunity["reasons"])})
            engine.set_state(review_action,review_record,"NOT_READY")
            continue
        if not fields.get("business_name"):
            engine.set_state(action,record,"INFORMATION_REQUIRED")
            record.result_json = canonical({"missing":["business_name"],"reason":"Save your business name once in the consented Business Passport."})
            engine.set_state(review_action,review_record,"NOT_READY")
            continue
        source = {"classification":"INTERNAL_APPLICATION_PREPARATION_NOT_OFFICIAL_FORM",
                  "business_name":fields["business_name"], "municipality":fields.get("municipality",""),
                  "concept":facts["concept"], "jurisdiction":facts["jurisdiction"],
                  "requested_cents":profile["amount_cents"], "use_of_funds":profile["use_of_funds"],
                  "plan":plan, "opportunity":opportunity,
                  "missing_for_real_application":opportunity["application_requirements"],
                  "eligibility":"PRELIMINARY_NOT_LEGAL_OR_LENDER_VERIFICATION",
                  "notice":"Unsigned private worksheet. Never submitted; no funding promised. Confirm current program form/terms with provider."}
        content = canonical(source); digest = sha(content.encode())
        older = next((a for a in previous if a.opportunity_id == opportunity["id"]),None)
        if not older or older.content_hash != digest:
            for task in review_tasks:
                task.status = "todo"
            older = FundingApplication(project_id=p.id,user_id=user.id,tenant_id=user.tenant_id,
                opportunity_id=opportunity["id"],revision=(older.revision + 1 if older else 1),
                source_json=content,content_hash=digest)
            db.add(older); db.flush()
        save_output(db,user,p,action,record,{"application_id":older.id,"revision":older.revision,
                    "content_hash":older.content_hash,"scope":"PRIVATE_PREPARATION_NOT_SUBMITTED"})
        engine.set_state(review_action,review_record,
            "COMPLETED_VERIFIED" if older.approved_hash == older.content_hash else "AWAITING_CUSTOMER_APPROVAL")
    db.flush()
