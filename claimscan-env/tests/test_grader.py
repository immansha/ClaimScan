from __future__ import annotations

from graders.base_grader import ClaimGroundTruth, DEFAULT_CONFIG, score_claim
from models import Action


def test_perfect_claim_scores_one():
    truth = ClaimGroundTruth(
        covered=True,
        payout=1500.0,
        fraud_rules=["F1", "F3"],
        priority="P2",
    )
    action = Action(
        covered=True,
        payout=1500.0,
        fraud_rules=["F3", "F1"],
        priority="P2",
    )

    breakdown = score_claim(action, truth, config=DEFAULT_CONFIG)
    assert abs(breakdown.total - 1.0) < 1e-6


def test_partial_claim_scores_fraction():
    truth = ClaimGroundTruth(
        covered=True,
        payout=1500.0,
        fraud_rules=["F1"],
        priority="P3",
    )
    action = Action(
        covered=False,
        payout=1500.0,
        fraud_rules=[],
        priority="P3",
    )

    breakdown = score_claim(action, truth, config=DEFAULT_CONFIG)
    # payout and priority correct only
    assert abs(breakdown.total - 0.5) < 1e-6

