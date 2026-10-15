"""Read-only official-information adapter; consequential providers remain gated."""
import json
from datetime import datetime, timezone
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

PUBLIC_FEED = "https://www.federalregister.gov/api/v1/documents.json?per_page=3&order=newest&conditions%5Bterm%5D=cleaning"


def connection_records():
    return [
        {"key": "federal_register", "name": "Federal Register public notices",
         "status": "READ_ONLY_ADAPTER_AVAILABLE", "cost": "PUBLIC_NO_CREDENTIALS",
         "next_dependency": "Customer-initiated connectivity check; notices are not applicability determinations."},
        {"key": "government_submission", "name": "Government DirectSubmit",
         "status": "NO_SUBMISSION_ADAPTER", "cost": "UNVERIFIED",
         "next_dependency": "Choose exact form/agency; verify accepted submission channel, required agreement, sandbox, credentials and fees."},
        {"key": "electronic_signature", "name": "Electronic signature provider",
         "status": "STANDBY_NOT_CONNECTED", "cost": "OWNER_PRICING_APPROVAL_REQUIRED",
         "next_dependency": "Select provider, verify pricing, authorize account/scopes and test signature/webhook evidence."},
        {"key": "professional_partner", "name": "Professional partner execution",
         "status": "EXISTING_PRIVATE_NETWORK_ONLY", "cost": "OWNER_PRICING_APPROVAL_REQUIRED",
         "next_dependency": "Existing Partner Network agreement, evidence, customer sharing consent and tested handoff."},
        {"key": "live_ai", "name": "Live AI consultant",
         "status": "STANDBY_NOT_ACTIVATED", "cost": "OWNER_PRICING_APPROVAL_REQUIRED",
         "next_dependency": "Explicit owner budget approval and provider configuration; do not label templates as AI."},
        {"key": "email", "name": "External document delivery",
         "status": "STANDBY_NOT_CONNECTED", "cost": "OWNER_PRICING_APPROVAL_REQUIRED",
         "next_dependency": "Verified sender/provider, confirmed no-cost entitlement or pricing approval, and exact recipient/sharing consent."},
        {"key": "payments", "name": "Existing payment foundations",
         "status": "PRESERVED_NOT_ACTIVATED", "cost": "OWNER_PRICING_APPROVAL_REQUIRED",
         "next_dependency": "Preserve Square; verified provider account, approved fees and separate customer charge approval."},
    ]


def fetch_public_notices():
    """Fixed public query: no business/customer fields, no credentials, no filings."""
    checked = datetime.now(timezone.utc).isoformat()
    try:
        req = Request(PUBLIC_FEED, headers={"Accept": "application/json", "User-Agent": "BIG-Public-Information/1.0"})
        with urlopen(req, timeout=6) as r:
            if urlsplit(r.geturl()).hostname != "www.federalregister.gov":
                raise ValueError("Unexpected public feed host")
            raw = r.read(262145)
            if len(raw) > 262144:
                raise ValueError("Public response exceeds safety limit")
            data = json.loads(raw)
        notices = []
        for item in data["results"][:3]:
            url = item["html_url"]
            parsed = urlsplit(url)
            if parsed.scheme != "https" or parsed.hostname != "www.federalregister.gov":
                continue
            notices.append({"title": str(item["title"])[:1000], "url": url,
                            "publication_date": str(item["publication_date"])[:10],
                            "document_number": str(item["document_number"])[:80]})
        return {"status": "PUBLIC_READ_VERIFIED", "checked_at": checked, "notices": notices,
                "notice": "Live public notices for a generic cleaning query; not personalized legal advice or a submission connection."}
    except Exception:
        return {"status": "UNAVAILABLE_NOT_VERIFIED", "checked_at": checked, "notices": [],
                "notice": "The official feed could not be verified. No external action occurred; use official reference links."}
