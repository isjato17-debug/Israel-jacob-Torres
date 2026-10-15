"""Strict recommendation boundary and no-network simulation for the future AI integration."""
from typing import Literal, Protocol
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .official_resources import RESOURCE_IDS
from .consultation_locales import COPY

MAX_TURNS = 8
MAX_MESSAGE_CHARS = 1200


class RoadmapStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=160)
    explanation: str = Field(min_length=1, max_length=1600)


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    mode: Literal["SIMULATION"]
    classification: Literal["SIMULATED_NOT_AI_GENERATED"]
    summary: str = Field(min_length=1, max_length=3000)
    next_question: str = Field(min_length=1, max_length=300)
    roadmap: list[RoadmapStep] = Field(min_length=1, max_length=5)
    assumptions: list[str] = Field(max_length=6)
    professional_review: list[str] = Field(min_length=1, max_length=5)
    source_ids: list[str] = Field(max_length=8)

    @field_validator("source_ids")
    @classmethod
    def only_curated_sources(cls, value):
        if any(item not in RESOURCE_IDS for item in value):
            raise ValueError("Unknown official resource")
        return value

    @field_validator("assumptions", "professional_review")
    @classmethod
    def bounded_text(cls, value):
        if any(not item.strip() or len(item) > 1200 for item in value):
            raise ValueError("Invalid recommendation text")
        return value


class ConsultationProvider(Protocol):
    def recommend(self, *, context: dict, message: str, turn: int) -> Recommendation: ...


class SimulationProvider:
    """Deterministic fixture with customer context. Never described as genuine AI."""
    def recommend(self, *, context, message, turn):
        text = COPY[context["language"]]
        detailed = context["detail_mode"] == "details"
        facts = context["answers"]
        stage = context["stage"]
        explanation = text["explanation"]
        if detailed:
            explanation += text["context"].format(**facts)
        return Recommendation(
            mode="SIMULATION", classification="SIMULATED_NOT_AI_GENERATED",
            summary=text["summary"].format(goal=facts["goal"]),
            next_question=text["questions"][min(turn, MAX_TURNS - 1)],
            roadmap=[RoadmapStep(title=text["actions"][stage], explanation=explanation)],
            assumptions=[text["assumption"]], professional_review=[text["professional"]],
            source_ids=["sba-launch", "sba-local", "irs-ein"] if stage == "start"
            else ["sba-local", "sba-loans", "irs-business"],
        )


def get_consultation_provider() -> ConsultationProvider:
    # Dependency injection supports offline fault tests. No client-supplied provider selection.
    return SimulationProvider()
