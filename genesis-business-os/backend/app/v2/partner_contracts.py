"""Private partner application contracts; never request provider secrets or ID documents."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from .catalog import STATES

CATEGORIES = [
    ("government_authorized", "Government-authorized service providers"),
    ("formation", "Business formation companies"), ("registered_agent", "Registered-agent providers"),
    ("legal", "Attorneys and legal professionals"), ("cpa", "Certified public accountants"),
    ("tax", "Tax professionals"), ("insurance", "Insurance providers"),
    ("banking_lending", "Banking and lending providers"),
    ("payroll_accounting", "Payroll and accounting providers"),
    ("intellectual_property", "Trademark and patent professionals"),
    ("ai_technology", "AI and technology providers"), ("marketing_growth", "Marketing and growth partners"),
]
STATUSES = ["APPLICATION", "UNDER_REVIEW", "VERIFICATION_REQUIRED", "VERIFIED",
            "AGREEMENT_PENDING", "APPROVED", "INTEGRATION_TESTING", "ACTIVE", "SUSPENDED", "REJECTED"]
JURISDICTIONS = [*STATES, ("DC", "Washington, DC")]
CAPABILITIES = {"external_actions": False, "public_directory": False, "live_integrations": False}


class PartnerInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    business_name: str = Field(min_length=2, max_length=160)
    contact_name: str = Field(min_length=2, max_length=160)
    contact_email: EmailStr = Field(max_length=254)
    category: str
    services: str = Field(min_length=5, max_length=2000)
    coverage: list[str] = Field(min_length=1, max_length=51)
    professional_credentials: str = Field(default="", max_length=2000)
    license_information: str = Field(default="", max_length=2000)
    api_capabilities: str = Field(default="", max_length=2000)
    partnership_interests: str = Field(default="", max_length=2000)
    pricing_information: str = Field(default="", max_length=2000)
    consent: Literal[True]

    @field_validator("*", mode="before")
    @classmethod
    def trim_strings(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("category")
    @classmethod
    def category_known(cls, value):
        if value not in dict(CATEGORIES):
            raise ValueError("Choose a supported partner category")
        return value

    @field_validator("coverage")
    @classmethod
    def valid_coverage(cls, value):
        if len(value) != len(set(value)) or any(code not in dict(JURISDICTIONS) for code in value):
            raise ValueError("Choose unique state/DC coverage codes")
        return value


class PartnerUpdate(PartnerInput):
    expected_version: int = Field(ge=1, strict=True)


class PartnerReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)
    action: Literal["begin_review", "request_information", "verify", "await_agreement",
                    "record_agreement", "approve", "begin_integration", "record_integration",
                    "activate", "suspend", "reject", "reopen"]
    confirm: Literal[True]
    reference: str = Field(default="", max_length=500)
    note: str = Field(default="", max_length=2000)

    @field_validator("reference", "note", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class PromotionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    partner_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=3, max_length=160)
    content: str = Field(min_length=5, max_length=6000)
    partner_permission_reference: str = Field(default="", max_length=500)
    consent: Literal[True]

    @field_validator("*", mode="before")
    @classmethod
    def trim(cls, value):
        return value.strip() if isinstance(value, str) else value


class PromotionReview(BaseModel):
    model_config = ConfigDict(extra="forbid")
    expected_version: int = Field(ge=1, strict=True)
    action: Literal["approve", "archive"]
    confirm: Literal[True]
