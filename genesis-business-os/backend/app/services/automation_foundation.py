"""Pure planning contracts. No scheduler, worker, credential access or external tools."""
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType


class WorkflowState(StrEnum):
    DRAFT = "DRAFT"
    AWAITING_REVIEW = "AWAITING_REVIEW"
    APPROVED_PLAN = "APPROVED_PLAN"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class AgentPolicy:
    name: str
    permissions: frozenset[str] = frozenset({"read_consented_context", "prepare_draft"})
    external_actions: bool = False
    paid_usage_limit_cents: int = 0
    status: str = "PLANNED_NOT_ACTIVE"


AGENTS = MappingProxyType({
    key: AgentPolicy(name=f"B.I.G. {name}") for key, name in [
        ("commander", "Commander"), ("marketing", "Marketing"), ("growth", "Growth"),
        ("finance", "Finance"), ("compliance", "Compliance"),
        ("intellectual_property", "Intellectual Property"), ("operations", "Operations"),
        ("customer_support", "Customer Support"), ("security", "Security"),
    ]
})
TRANSITIONS = {
    (WorkflowState.DRAFT, "request_review"): WorkflowState.AWAITING_REVIEW,
    (WorkflowState.AWAITING_REVIEW, "owner_approve_plan"): WorkflowState.APPROVED_PLAN,
    (WorkflowState.AWAITING_REVIEW, "reject"): WorkflowState.DRAFT,
}


def transition(state: WorkflowState, event: str, *, owner_approved=False) -> WorkflowState:
    if event == "cancel":
        return WorkflowState.CANCELLED
    if event == "dependency_failed":
        return WorkflowState.BLOCKED
    if event == "retry" and state == WorkflowState.BLOCKED:
        # Recovery always requires review again, never autonomous redispatch.
        return WorkflowState.DRAFT
    if event == "owner_approve_plan" and not owner_approved:
        raise PermissionError("Owner review required")
    try:
        return TRANSITIONS[(state, event)]
    except KeyError:
        raise ValueError("Unsupported planning transition") from None


@dataclass(frozen=True)
class RevenueEvidence:
    """Future server-verified payment ledger input, not user estimates or campaign budgets."""
    collected_cents: int
    refunded_cents: int
    processing_fee_cents: int
    restricted_cents: int  # tax, government fees and provider liabilities
    verified: bool = False


def planned_ai_budget(evidence: RevenueEvidence, allocation_bps=500):
    values = (evidence.collected_cents, evidence.refunded_cents,
              evidence.processing_fee_cents, evidence.restricted_cents, allocation_bps)
    if any(type(value) is not int or value < 0 for value in values) or allocation_bps > 500:
        raise ValueError("Use integer cents and an owner-reviewed allocation up to 5%")
    eligible = max(0, evidence.collected_cents - evidence.refunded_cents -
                   evidence.processing_fee_cents - evidence.restricted_cents) if evidence.verified else 0
    return {
        "eligible_cents": eligible, "allocation_bps": allocation_bps,
        "planning_limit_cents": eligible * allocation_bps // 10000,
        "spend_authorized_cents": 0, "per_agent_live_limit_cents": 0,
        "alert": "LIVE_USAGE_BLOCKED",
    }


def enforce_agent_permission(agent: str, permission: str, proposed_cost_cents=0):
    if agent not in AGENTS or permission not in AGENTS[agent].permissions:
        raise PermissionError("Agent permission denied")
    if type(proposed_cost_cents) is not int or proposed_cost_cents != 0:
        raise PermissionError("Paid usage is not authorized")
