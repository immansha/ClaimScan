from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


PolicyType = Literal["auto", "home", "health"]
PriorityType = Literal["P1", "P2", "P3", "P4"]


class Observation(BaseModel):
    """Observation provided to the agent at each step."""

    claim_id: str
    customer_id: str
    tenure_days: int
    past_claims_12m: int
    policy_type: PolicyType
    policy_limit: float
    policy_start_date: str
    covered_damages: List[str]
    damage_type: str
    incident_date: str
    filing_date: str
    claim_amount: float
    deductible: float
    required_docs: List[str]
    docs_submitted: List[str]
    avg_amount_for_damage_type: float
    queue_position: int
    queue_length: int
    steps_remaining: int
    previous_reward: float


class Action(BaseModel):
    """Action the agent must take for a claim."""

    covered: bool = Field(..., description="Whether the claim damage is covered by the policy.")
    payout: float = Field(..., ge=0.0, description="Calculated payout amount for this claim.")
    fraud_rules: List[str] = Field(
        default_factory=list,
        description="List of fraud rule identifiers triggered for this claim (e.g. ['F1', 'F3']).",
    )
    priority: PriorityType = Field(..., description="Priority code (P1-P4).")

    @field_validator("fraud_rules", mode="before")
    @classmethod
    def normalize_fraud_rules(cls, v: Optional[List[str]]) -> List[str]:
        if v is None:
            return []
        # Deduplicate and sort for deterministic comparisons
        unique = sorted({str(rule).upper() for rule in v})
        return unique


class RewardBreakdown(BaseModel):
    """Detailed reward components for debugging and graders."""

    coverage_correct: float
    payout_correct: float
    fraud_rules_correct: float
    priority_correct: float
    connected_fraud_bonus: float = 0.0
    total: float

