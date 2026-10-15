"""Bounded, customer-initiated official-source reads; never automatic legal applicability."""
import html
import re
from urllib.request import Request, urlopen
from urllib.parse import urlsplit
from .external_readiness import fetch_public_notices

NY_WAGE_URL = "https://dol.ny.gov/minimum-wage"
LEGAL_STATES = ("PROPOSED", "ENACTED", "EFFECTIVE", "SUPERSEDED", "REPEALED", "UNVERIFIED")


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
