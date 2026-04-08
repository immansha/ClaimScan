from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, List, Set

from models import Observation

DATE_FMT = "%Y-%m-%d"


def _parse_date(date_str: str) -> datetime:
    return datetime.strptime(date_str, DATE_FMT)


@dataclass(frozen=True)
class FraudContext:
    """Context across the current episode queue for connected fraud checks."""

    all_claims: Iterable[Observation]


def rule_f1(observation: Observation) -> bool:
    """F1: Filed within 7 days of policy start date."""

    start = _parse_date(observation.policy_start_date)
    filing = _parse_date(observation.filing_date)
    delta_days = (filing - start).days
    return 0 <= delta_days <= 7


def rule_f2(observation: Observation) -> bool:
    """F2: Customer has 3+ claims in last 12 months."""

    return observation.past_claims_12m >= 3


def rule_f3(observation: Observation) -> bool:
    """F3: Claim amount > $10,000 AND customer tenure < 30 days."""

    return observation.claim_amount > 10_000 and observation.tenure_days < 30


def rule_f4(observation: Observation) -> bool:
    """F4: Incident date > filing date (future dated claim)."""

    incident = _parse_date(observation.incident_date)
    filing = _parse_date(observation.filing_date)
    return incident > filing


def rule_f5(observation: Observation, context: FraudContext) -> bool:
    """F5: Same customer ID appears in 2+ claims in current queue (connected fraud)."""

    customer_id = observation.customer_id
    count = sum(1 for claim in context.all_claims if claim.customer_id == customer_id)
    return count >= 2


def rule_f6(observation: Observation) -> bool:
    """F6: Claim amount > 2x average for this damage type."""

    return observation.claim_amount > 2 * observation.avg_amount_for_damage_type


def rule_f7(observation: Observation) -> bool:
    """F7: Missing required document (police report for theft > $5000)."""

    if observation.damage_type != "theft":
        return False
    if observation.claim_amount <= 5_000:
        return False
    required = "police_report"
    return required in observation.required_docs and required not in observation.docs_submitted


def evaluate_fraud_rules(observation: Observation, context: FraudContext) -> List[str]:
    """Return the sorted list of fraud rule IDs triggered for this observation."""

    triggered: Set[str] = set()

    if rule_f1(observation):
        triggered.add("F1")
    if rule_f2(observation):
        triggered.add("F2")
    if rule_f3(observation):
        triggered.add("F3")
    if rule_f4(observation):
        triggered.add("F4")
    if rule_f5(observation, context):
        triggered.add("F5")
    if rule_f6(observation):
        triggered.add("F6")
    if rule_f7(observation):
        triggered.add("F7")

    return sorted(triggered)

