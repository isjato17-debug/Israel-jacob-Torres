"""Curated navigation only. No API connections, legal determinations or live status claims."""
from pydantic import BaseModel, ConfigDict
from typing import Literal
from .resource_locales import TITLES


class OfficialResource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    id: str
    title: str
    url: str
    kind: Literal["OFFICIAL_RESOURCE"] = "OFFICIAL_RESOURCE"
    verification: Literal["REFERENCE_ONLY_NOT_STATUS_VERIFICATION"] = "REFERENCE_ONLY_NOT_STATUS_VERIFICATION"


RESOURCES = (
    OfficialResource(id="sba-launch", title="SBA — launch your business", url="https://www.sba.gov/counseling/launch-your-business/"),
    OfficialResource(id="irs-ein", title="IRS — EIN guidance", url="https://www.irs.gov/businesses/small-businesses-self-employed/get-an-employer-identification-number"),
    OfficialResource(id="uspto-trademarks", title="USPTO — trademark research", url="https://www.uspto.gov/trademarks"),
    OfficialResource(id="uspto-patents", title="USPTO — patent research", url="https://www.uspto.gov/patents"),
    OfficialResource(id="copyright", title="U.S. Copyright Office — registration guidance", url="https://www.copyright.gov/registration/"),
    OfficialResource(id="fincen", title="FinCEN — official resources (check current applicability)", url="https://www.fincen.gov/"),
    OfficialResource(id="irs-business", title="IRS — business tax resources", url="https://www.irs.gov/businesses"),
    OfficialResource(id="sba-permits", title="SBA — locate applicable licenses and permits", url="https://www.sba.gov/counseling/launch-your-business/#licenses-permits"),
    OfficialResource(id="sba-local", title="SBA — local assistance, SBDC and SCORE mentoring", url="https://www.sba.gov/counseling/local-assistance/"),
    OfficialResource(id="sba-loans", title="SBA — loan programs and lender eligibility requirements", url="https://www.sba.gov/loans/"),
    OfficialResource(id="sba-guide", title="SBA — business counseling and training", url="https://www.sba.gov/counseling/"),
)
RESOURCE_IDS = {item.id for item in RESOURCES}


def public_resources(language="en"):
    titles = TITLES.get(language, {})
    return [{**item.model_dump(), "title": titles.get(item.id, item.title)} for item in RESOURCES]


# Adapter boundaries for future verified coverage; no invented agency URLs or coverage.
PLANNED_JURISDICTION_ADAPTERS = ("state_registration", "state_licensing", "local_agencies", "federal_regulators")
