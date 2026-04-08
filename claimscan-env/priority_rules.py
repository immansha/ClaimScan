from __future__ import annotations

from typing import Iterable, List

from models import PriorityType


def calculate_priority(claim_amount: float, fraud_rules: Iterable[str]) -> PriorityType:
    """Compute P1-P4 according to the deterministic rules.

    P1: Any fraud rule triggered AND claim amount > $5,000
    P2: Any fraud rule triggered OR claim amount > $10,000
    P3: No fraud rules, claim amount $1,000-$10,000
    P4: No fraud rules, claim amount < $1,000
    """

    fraud_list: List[str] = list(fraud_rules)
    has_fraud = len(fraud_list) > 0

    if has_fraud and claim_amount > 5_000:
        return "P1"
    if has_fraud or claim_amount > 10_000:
        return "P2"
    if not has_fraud and 1_000 <= claim_amount <= 10_000:
        return "P3"
    # Includes both < 1_000 and any degenerate case; specification only covers < 1_000 explicitly.
    return "P4"

