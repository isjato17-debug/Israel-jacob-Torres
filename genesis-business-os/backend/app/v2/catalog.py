"""Service discovery, not a claim of government or provider API access."""

STATES = [
    ("AL", "Alabama"), ("AK", "Alaska"), ("AZ", "Arizona"), ("AR", "Arkansas"),
    ("CA", "California"), ("CO", "Colorado"), ("CT", "Connecticut"), ("DE", "Delaware"),
    ("FL", "Florida"), ("GA", "Georgia"), ("HI", "Hawaii"), ("ID", "Idaho"),
    ("IL", "Illinois"), ("IN", "Indiana"), ("IA", "Iowa"), ("KS", "Kansas"),
    ("KY", "Kentucky"), ("LA", "Louisiana"), ("ME", "Maine"), ("MD", "Maryland"),
    ("MA", "Massachusetts"), ("MI", "Michigan"), ("MN", "Minnesota"), ("MS", "Mississippi"),
    ("MO", "Missouri"), ("MT", "Montana"), ("NE", "Nebraska"), ("NV", "Nevada"),
    ("NH", "New Hampshire"), ("NJ", "New Jersey"), ("NM", "New Mexico"), ("NY", "New York"),
    ("NC", "North Carolina"), ("ND", "North Dakota"), ("OH", "Ohio"), ("OK", "Oklahoma"),
    ("OR", "Oregon"), ("PA", "Pennsylvania"), ("RI", "Rhode Island"), ("SC", "South Carolina"),
    ("SD", "South Dakota"), ("TN", "Tennessee"), ("TX", "Texas"), ("UT", "Utah"),
    ("VT", "Vermont"), ("VA", "Virginia"), ("WA", "Washington"), ("WV", "West Virginia"),
    ("WI", "Wisconsin"), ("WY", "Wyoming"),
]
ENTITY_TYPES = ["LLC", "Corporation", "Partnership", "Nonprofit", "Sole proprietorship"]
OWNERSHIP_TYPES = ["Independent business", "Holding company", "Subsidiary"]
SBA = "https://www.sba.gov/counseling/launch-your-business/"
IRS = "https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number"

# key, stage, title, description, availability, review, official guidance
SERVICES = [
    ("formation", "start", "Business formation", "Review entity structure and state registration requirements.", "GUIDED_ONLY", True, SBA),
    ("ein", "start", "EIN & tax registration", "Prepare for the official IRS EIN process and applicable tax registrations.", "GUIDED_ONLY", True, IRS),
    ("licenses", "start", "Licenses & permits", "Identify state, local and industry-specific requirements.", "GUIDED_ONLY", True, SBA),
    ("registered_agent", "start", "Registered agent", "Select a qualified agent where the entity and state require one.", "NEEDS_CONNECTION", True, None),
    ("legal", "start", "Legal documents & IP", "Coordinate contracts, intellectual property and licensed legal review.", "NEEDS_PROFESSIONAL", True, None),
    ("banking", "start", "Business banking", "Prepare account-opening information; bank KYC remains mandatory.", "NEEDS_CONNECTION", False, None),
    ("bookkeeping", "run", "Accounting & bookkeeping", "Organize books and coordinate accounting professionals.", "NEEDS_CONNECTION", True, None),
    ("invoicing", "run", "Invoicing & payments", "Connect payments and reconcile provider-confirmed transactions.", "NEEDS_CONNECTION", False, None),
    ("payroll", "run", "Payroll", "Coordinate payroll, withholding and employee reporting.", "NEEDS_CONNECTION", True, None),
    ("insurance", "run", "Business insurance", "Identify coverage needs with a licensed insurance professional.", "NEEDS_PROFESSIONAL", True, None),
    ("compliance", "run", "Compliance management", "Review recurring state, federal and local obligations.", "GUIDED_ONLY", True, SBA),
    ("customers", "run", "Customer management", "Connect customer records and consent-based communications.", "NEEDS_CONNECTION", False, None),
    ("website", "grow", "Website, domain & email", "Coordinate a business website, domain and business email.", "NEEDS_CONNECTION", False, None),
    ("brand", "grow", "Branding & marketing", "Prepare positioning and campaigns before approving spend.", "GUIDED_ONLY", False, SBA),
    ("commerce", "grow", "E-commerce", "Connect storefront, order and fulfillment services.", "NEEDS_CONNECTION", False, None),
    ("financing", "grow", "Financing & business credit", "Review resources; no funding eligibility or approval is guaranteed.", "NEEDS_PROFESSIONAL", True, None),
    ("expansion", "grow", "Growth & expansion", "Plan capacity, new markets and subsidiary structures with professional review.", "GUIDED_ONLY", True, SBA),
]


def service_records():
    return [
        dict(id=key, stage=stage, title=title, description=description,
             availability=availability, professional_review=review,
             official_url=url, price_cents=None, submission_available=False)
        for key, stage, title, description, availability, review, url in SERVICES
    ]
