from __future__ import annotations

from models import Observation


def calculate_payout(observation: Observation) -> float:
    """Deterministically compute payout for a claim.

    payout = min(max(claim_amount - deductible, 0), policy_limit)
    """

    gross = max(observation.claim_amount - observation.deductible, 0.0)
    payout = min(gross, observation.policy_limit)
    # Round to cents for deterministic comparison
    return round(payout, 2)

