"""Reviewed public source snapshots, NOT live program availability or verified eligibility.

Directories are explicitly not grants or loan offers. No application service/account is activated.
"""
from datetime import date, datetime, timezone

CHECKED = "2026-10-16"
IMMIGRATION_SOURCE = "https://www.uscis.gov/working-in-the-united-states/entrepreneur-employment-pathways/immigrant-pathways-for-entrepreneur-employment-in-the-united-states"
SBA_CITIZENSHIP_SOURCE = "https://www.sba.gov/article/2026/03/09/sba-bans-foreign-nationals-accessing-sba-backed-loans"
PROGRAMS = [
    {"id":"sba_microloan", "name":"SBA Microloan intermediary program", "kind":"LOAN",
     "category":"SBA_SUPPORTED", "source":"https://www.sba.gov/loans/microloans/",
     "additional_source":SBA_CITIZENSHIP_SOURCE, "requirements":[
         "U.S. small operating for-profit business; intermediary underwriting applies.",
         "Published March 9, 2026 SBA citizenship notice restricts ownership to U.S. citizens/nationals with principal U.S. residence; confirm current lender policy.",
         "Loan proceeds, collateral, guarantees, rate and repayment terms require lender review."],
     "application_requirements":["Business plan", "Use-of-funds budget", "Lender-requested financials and identity verification outside B.I.G."],
     "deadline_rule":"Intermediary-specific; no universal deadline verified", "fee_cents":None},
    {"id":"kiva_us", "name":"Kiva U.S. community-funded business loans", "kind":"LOAN",
     "category":"NONPROFIT", "source":"https://www.kiva.org/borrow", "requirements":[
         "Applicant at least 18, residing and operating in the U.S.; business cannot be registered or primarily operate in Nevada or North Dakota.",
         "Provider must check business-purpose, industry and other eligibility exclusions directly; B.I.G. does not collect criminal history or credit reports.",
         "Social underwriting and successful private/public fundraising required; no funding guarantee.",
         "Published 0% interest, no fees and no collateral; term and loan amount require a specific offer."],
     "application_requirements":["Business story", "Use-of-funds budget", "Social underwriting plan", "Provider eligibility review"],
     "deadline_rule":"Provider and fundraising-cycle specific", "fee_cents":0},
    {"id":"amber_grant", "name":"WomensNet Amber Grant", "kind":"GRANT",
     "category":"PRIVATE_GRANT", "source":"https://ambergrantsforwomen.com/faq/", "requirements":[
         "Woman applicant age 18 or older; business at least 50% women-owned and based in U.S. or Canada.",
         "Competitive selection; grant receipt is not guaranteed.",
         "FAQ contains inconsistent award amounts; award size must be confirmed directly.",
         "Published $15 application fee; waiver may be requested. B.I.G. will not pay or apply."],
     "application_requirements":["Business story", "Plans for business growth", "Detailed grant use", "Confirm eligibility and current cycle"],
     "deadline_rule":"FAQ states last day of month 11:59:59 p.m. Eastern; confirm current cycle", "fee_cents":1500},
    {"id":"federal_grants", "name":"Grants.gov federal opportunity search", "kind":"DIRECTORY",
     "category":"FEDERAL_GRANTS", "source":"https://simpler.grants.gov/search",
     "requirements":["Each actual award has its own eligible applicant types, purpose, dates and registration requirements.",
                     "A directory result is not a grant award or a finding that ordinary startup expenses qualify."],
     "application_requirements":["Select an actual funding notice", "Verify awarding-agency requirements and deadlines"],
     "deadline_rule":"Specific funding notice required", "fee_cents":None},
    {"id":"ny_state_local", "name":"New York ESD small-business and immigrant entrepreneur resources", "kind":"DIRECTORY",
     "category":"STATE_LOCAL_GRANTS_AND_FINANCING", "source":"https://esd.ny.gov/doing-business-ny/small-business-hub",
     "requirements":["Select a specific state/local program; location, purpose and operating history may apply.",
                     "The resource hub is not itself an open grant. Immigrant resources do not grant work authorization."],
     "application_requirements":["Select and verify a named program", "Confirm locality and activity"],
     "deadline_rule":"Specific program required", "fee_cents":None},
    {"id":"cdfi", "name":"U.S. Treasury CDFI awardee directory", "kind":"DIRECTORY",
     "category":"COMMUNITY_DEVELOPMENT_LENDERS", "source":"https://www.cdfifund.gov/awards/state-awards",
     "requirements":["Directory identifies organizations, not individual business loan offers.",
                     "Confirm lender products, service area, borrower eligibility and current terms directly."],
     "application_requirements":["Select a community lender", "Obtain a specific term sheet"],
     "deadline_rule":"Lender-specific", "fee_cents":None},
    {"id":"credit_unions", "name":"NCUA credit union locator", "kind":"DIRECTORY",
     "category":"CREDIT_UNIONS_AND_LENDERS", "source":"https://mapping.ncua.gov/",
     "requirements":["Membership and business-lending availability are institution-specific.",
                     "A listing does not establish loan approval, APR or immigrant eligibility."],
     "application_requirements":["Confirm membership and business lending", "Obtain a written quote"],
     "deadline_rule":"Institution-specific", "fee_cents":None},
]


def match(profile, jurisdiction):
    stale = not 0 <= (datetime.now(timezone.utc).date() - date.fromisoformat(CHECKED)).days <= 30
    results = []
    for program in PROGRAMS:
        status, reasons = "UNCERTAIN_REVIEW_REQUIRED", ["Published criteria do not certify individual eligibility."]
        missing = []
        if program["kind"] == "DIRECTORY":
            status = "DISCOVERY_DIRECTORY_NOT_AWARD"
        else:
            screening_fields = ("us_resident",) if program["id"] == "sba_microloan" else ("adult",) if program["id"] == "amber_grant" else ("adult", "us_resident")
            for field in screening_fields:
                if profile.get(field) is None:
                    missing.append(field)
                elif profile[field] is False:
                    status = "INELIGIBLE_PUBLISHED_CRITERION"
                    reasons.append(f"Declared {field.replace('_',' ')} does not meet this program's published criterion.")
            field = "all_owners_us_citizens_or_nationals" if program["id"] == "sba_microloan" else "women_owned_50_percent" if program["id"] == "amber_grant" else None
            if field:
                if profile.get(field) is None:
                    missing.append(field)
                elif profile[field] is False:
                    status = "INELIGIBLE_PUBLISHED_CRITERION"
                    reasons.append(f"Declared {field.replace('_',' ')} does not meet the published screening criterion.")
            if status != "INELIGIBLE_PUBLISHED_CRITERION" and not missing:
                status = "POTENTIAL_MATCH_NOT_VERIFIED"
            if program["id"] == "kiva_us" and jurisdiction in ("NV", "ND"):
                status = "INELIGIBLE_PUBLISHED_CRITERION"
                reasons.append("Saved operating jurisdiction is excluded by Kiva's published Nevada/North Dakota criterion.")
            if stale:
                status = "SOURCE_STALE_REVERIFY_REQUIRED"
        if program["id"] == "ny_state_local" and jurisdiction != "NY":
            reasons.append("This directory is for New York; use the actual state's agencies for other locations.")
        results.append({**program, "checked_at":CHECKED, "source_status":"STALE" if stale else "PUBLIC_SOURCE_REVIEWED",
                        "current_status":"LIVE_APPLICATION_AVAILABILITY_UNVERIFIED", "match_status":status,
                        "missing":missing, "reasons":reasons, "deadline":None,
                        "submission_status":"BLOCKED_NO_APPROVED_INTEGRATION",
                        "eligibility_verification":"NOT_CERTIFIED"})
    return results
