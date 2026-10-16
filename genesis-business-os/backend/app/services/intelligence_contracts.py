"""Untrusted provider proposals are data, never permissions, receipts or executable code."""
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Tool = Literal["native:context", "native:requirements", "prepare",
               "tool:business_plan_prepare", "tool:offer_prepare", "tool:outreach_prepare",
               "tool:pricing_prepare", "tool:launch_checklist_prepare"]


class StrictContract(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class TaskProposal(StrictContract):
    tool: Tool
    reason: str = Field(min_length=1, max_length=1200)


class StrategyProposal(StrictContract):
    key: str = Field(min_length=1, max_length=60)
    title: str = Field(min_length=1, max_length=160)
    reasoning: str = Field(min_length=1, max_length=1800)


class RegulatoryClaim(StrictContract):
    source_url: str = Field(pattern=r"^https://", max_length=500)
    claim: str = Field(min_length=1, max_length=1200)
    verification: Literal["UNVERIFIED"]


class IntelligenceProposal(StrictContract):
    summary: str = Field(min_length=1, max_length=3000)
    strategies: list[StrategyProposal] = Field(min_length=2, max_length=2)
    recommended_strategy: str = Field(max_length=60)
    financial_plans: list[dict] = Field(min_length=3, max_length=3)
    risks: list[str] = Field(min_length=1, max_length=10)
    tasks: list[TaskProposal] = Field(min_length=1, max_length=8)
    regulatory_claims: list[RegulatoryClaim] = Field(default_factory=list, max_length=10)

    @model_validator(mode="after")
    def distinct(self):
        keys = [s.key for s in self.strategies]
        if len(set(keys)) != 2 or self.recommended_strategy not in keys:
            raise ValueError("Exactly two distinct strategies and a matching recommendation required")
        if len({t.tool for t in self.tasks}) != len(self.tasks):
            raise ValueError("Duplicate task proposals are not permitted")
        if any(not risk.strip() or len(risk) > 1200 for risk in self.risks):
            raise ValueError("Risk text is invalid")
        return self


class ProviderConfig(StrictContract):
    provider: Literal["mock", "openai_compatible_disabled"] = "mock"
    model: str = Field(default="deterministic-fixture-v1", min_length=1, max_length=100)
    timeout_seconds: float = Field(default=2.0, gt=0, le=10)
    max_attempts: int = Field(default=2, ge=1, le=3)
    max_output_tokens: int = Field(default=8000, ge=1, le=16000)


class StructuredRequest(StrictContract):
    correlation_id: str
    model: str
    context: dict
    response_schema: dict
    max_output_tokens: int
