"""Bounded, customer-initiated official-source reads; never automatic legal applicability."""
import html
import re
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from .external_readiness import fetch_public_notices

NY_WAGE_URL = "https://dol.ny.gov/minimum-wage"
LEGAL_STATES = ("PROPOSED", "ENACTED", "EFFECTIVE", "SUPERSEDED", "REPEALED", "UNVERIFIED")


def store_sources(db, user, p, items):
    """One recording path for manual and automatic bounded public reads."""
    from sqlalchemy import select
    from ..models import RegulatorySourceRevision, RegulatoryChangeRecord, ExecutionTask
    from . import business_orchestrator as engine
    from .document_engine import canonical
    from .test_signing import sha
    added = 0
    for item in items:
        facts = item["facts"]
        content_hash = sha(canonical(facts).encode())
        exists = db.scalar(select(RegulatorySourceRevision).where(
            RegulatorySourceRevision.project_id == p.id, RegulatorySourceRevision.source_key == item["key"],
            RegulatorySourceRevision.content_hash == content_hash))
        if exists:
            continue
        previous = db.scalar(select(RegulatorySourceRevision).where(
            RegulatorySourceRevision.project_id == p.id, RegulatorySourceRevision.source_key == item["key"])
                             .order_by(RegulatorySourceRevision.checked_at.desc()))
        source = RegulatorySourceRevision(project_id=p.id, source_key=item["key"], source_url=item["url"],
                                         facts_json=canonical(facts), content_hash=content_hash)
        db.add(source); db.flush()
        change = RegulatoryChangeRecord(project_id=p.id, source_revision_id=source.id,
            previous_revision_id=previous.id if previous else None,
            change_type="SOURCE_CONTENT_CHANGED" if previous else "FIRST_SOURCE_OBSERVATION",
            legal_status=facts["legal_status"], effective_date=facts.get("effective_date"))
        db.add(change); db.flush()
        action, record = engine.create_action(db, user, p, "regulatory:" + change.id,
            "Review official source: " + facts["title"], "Regulatory intelligence / Mission Control", [])
        engine.set_state(action, record, "AWAITING_CUSTOMER_APPROVAL")
        db.add(ExecutionTask(tenant_id=user.tenant_id, business_id=p.business_id, horizon="today",
            task="Review possible regulatory relevance: " + facts["title"], budget="0", kpi="regulatory:" + change.id))
        engine.evidence(db, user, p, action, "official_source_observed",
            "Official source collected; legal applicability NOT verified",
            {"source_hash": content_hash, "change_type": change.change_type})
        added += 1
    return added


def collect_sources():
    results, errors = [], []
    feed = fetch_public_notices()
    if feed["status"] == "PUBLIC_READ_VERIFIED":
        for notice in feed["notices"]:
            results.append({"key": "federal:" + notice["document_number"], "url": notice["url"],
                            "facts": {**notice, "jurisdiction": "US", "industry": "Unverified relevance to cleaning",
                                      "legal_status": "UNVERIFIED", "effective_date": None,
                                      "impact": "Review the official notice's scope and rule stage. A generic search match is not an obligation."}})
    else:
        errors.append("Federal Register unavailable; no new verified feed records")
    try:
        with urlopen(Request(NY_WAGE_URL, headers={"User-Agent": "BIG-Public-Information/1.0"}), timeout=6) as r:
            if urlsplit(r.geturl()).hostname != "dol.ny.gov":
                raise ValueError("Unexpected host")
            raw = r.read(524289)
            if len(raw) > 524288:
                raise ValueError("Oversized source")
        text = re.sub(r"\s+", " ", html.unescape(re.sub("<[^>]+>", " ", raw.decode("utf-8"))))
        # Preserve relevant exact source text, not an invented wage or enactment date.
        pos = text.find("Minimum Wage Updates")
        excerpt = text[pos:pos + 3000] if pos >= 0 else ""
        if not excerpt or "2027" not in excerpt or "minimum wage" not in excerpt.lower():
            raise ValueError("Source extraction changed")
        results.append({"key": "ny:minimum-wage-updates", "url": NY_WAGE_URL,
                        "facts": {"title": "New York minimum-wage guidance and 2027 update",
                                  "excerpt": excerpt, "jurisdiction": "NY", "industry": "Potential employers",
                                  "legal_status": "UNVERIFIED", "effective_date": None,
                                  "impact": "Human review required: distinguish current rates, future dates and any proposed changes. "
                                            "Confirm hiring, location and wage order; no personal deadline or wage rule is auto-applied."}})
    except Exception:
        errors.append("New York wage source unavailable or changed; no verified wage update recorded")
    return results, errors
