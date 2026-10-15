"""Verified official references, not invented government adapters or fillable forms."""
from . import document_engine

LLC = "https://dos.ny.gov/articles-organization-domestic-limited-liability-company-0"
CORP = "https://dos.ny.gov/certificate-incorporation-domestic-business-corporation"
COUNTY = "https://www.albanycountyny.gov/fees-forms"
CHECKED = "2026-10-15"


def registry():
    return [
        {**document_engine.definition(), "title": document_engine.TITLE, "category": "BIG_BUSINESS_DOCUMENT",
         "status": "SUPPORTED_UNSIGNED_AND_TEST_SIGNING", "source_url": None, "jurisdiction": "NY planning context",
         "eligibility": "Cleaning services; customer and professional review required",
         "passport_mapping": ["business_name", "representative_name", "business_email", "municipality"],
         "conditional_questions": [], "supporting_documents": [], "fees": "No B.I.G. provider charge activated",
         "signatures": "Blank manual blocks or explicitly test-only provider signature",
         "submission": "No receiving agency for a private cleaning agreement", "renewal": "Per parties' agreed terms"},
        {"key": "ny_llc_articles", "title": "NY LLC Articles of Organization — official reference",
         "category": "OFFICIAL_GOVERNMENT_REFERENCE", "status": "REFERENCE_ONLY_NOT_AUTOFILLABLE",
         "source_url": LLC, "jurisdiction": "New York", "source_checked": CHECKED,
         "official_form_version": "NOT_VERIFIED_FOR_AUTOFILL", "eligibility": "Domestic LLC; regulated professions need separate review",
         "required_fields": ["LLC name", "county", "service-of-process address", "organizer signature", "filer"],
         "conditional_questions": ["Restricted name consents", "Professional service eligibility"],
         "validation": "Agency review; no B.I.G. eligibility certification",
         "supporting_documents": ["Required consents if applicable"],
         "signatures": "Organizer must sign; agency method must be verified",
         "submission": "CUSTOMER_ASSISTED_OFFICIAL_PORTAL; no connected API",
         "fees": "$200 formation; $50 publication certificate plus variable newspaper costs; reverify before filing",
         "renewal": "Biennial statement; $9 fee; timing depends on actual filing date"},
    ]


def government_workflows():
    return [
        {"key": "ny_sole_proprietor", "title": "Sole proprietor / assumed-name certificate",
         "method": "CUSTOMER_ASSISTED_OFFICIAL_PORTAL", "fee": "County-specific; not verified",
         "source_url": COUNTY, "status": "COUNTY_REQUIREMENTS_REVIEW_NEEDED",
         "prerequisites": ["Confirm operating name and actual county", "County certificate/notarization, fee and delivery method",
                           "No Department of State entity formation implied", "Tax, EIN, permits and work authorization reviewed separately"]},
        {"key": "ny_llc", "title": "Domestic LLC — first candidate for customer-assisted integration",
         "method": "CUSTOMER_ASSISTED_OFFICIAL_PORTAL", "fee": "$200 plus applicable publication/other costs",
         "source_url": LLC, "status": "OFFICIAL_PORTAL_VERIFIED_API_NOT_VERIFIED",
         "prerequisites": ["Customer chooses structure after legal/financial review", "Name, county, process address, organizer signature",
                           "Publication within 120 days where required; operating agreement within 90 days",
                           "Actual official receipt required; no live adapter or portal automation enabled"]},
        {"key": "ny_corporation", "title": "Domestic business corporation",
         "method": "CUSTOMER_ASSISTED_OFFICIAL_PORTAL", "fee": "$125 base filing; verify additional applicable fees/taxes",
         "source_url": CORP, "status": "OFFICIAL_PORTAL_VERIFIED_API_NOT_VERIFIED",
         "prerequisites": ["Corporate name/purpose, county, share structure and process address",
                           "Incorporator signature and any agency consents", "Official receipt and ongoing biennial obligations"]},
    ]
