from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from pydantic import BaseModel

from models import Action, RewardBreakdown


class ClaimGroundTruth(BaseModel):
    covered: bool
    payout: float
    fraud_rules: List[str]
    priority: str


@dataclass
class ClaimScoreConfig:
    coverage_weight: float
    payout_weight: float
    fraud_weight: float
    priority_weight: float
    connected_bonus: float = 0.0


DEFAULT_CONFIG = ClaimScoreConfig(
    coverage_weight=0.25,
    payout_weight=0.25,
    fraud_weight=0.25,
    priority_weight=0.25,
    connected_bonus=0.0,
)


HARD_CONFIG = ClaimScoreConfig(
    coverage_weight=0.20,
    payout_weight=0.20,
    fraud_weight=0.20,
    priority_weight=0.20,
    connected_bonus=0.15,
)


def _fraud_sets_equal(pred: Iterable[str], truth: Iterable[str]) -> bool:
    return set(pred) == set(truth)


def score_claim(
    action: Action,
    ground_truth: ClaimGroundTruth,
    config: ClaimScoreConfig = DEFAULT_CONFIG,
    connected_fraud_all_flagged: bool | None = None,
) -> RewardBreakdown:
    """Score a single claim deterministically."""

    coverage_correct = config.coverage_weight if action.covered == ground_truth.covered else 0.0

    payout_correct = (
        config.payout_weight if abs(action.payout - ground_truth.payout) <= 0.01 else 0.0
    )

    fraud_correct = (
        config.fraud_weight
        if _fraud_sets_equal(action.fraud_rules, ground_truth.fraud_rules)
        else 0.0
    )

    priority_correct = (
        config.priority_weight if action.priority == ground_truth.priority else 0.0
    )

    connected_bonus = 0.0
    if config.connected_bonus > 0.0 and connected_fraud_all_flagged:
        connected_bonus = config.connected_bonus

    total = coverage_correct + payout_correct + fraud_correct + priority_correct + connected_bonus

    return RewardBreakdown(
        coverage_correct=coverage_correct,
        payout_correct=payout_correct,
        fraud_rules_correct=fraud_correct,
        priority_correct=priority_correct,
        connected_fraud_bonus=connected_bonus,
        total=total,
    )


def normalize_episode_scores(per_claim_scores: Sequence[float]) -> float:
    """Return the mean episode score in [0, 1]."""

    if not per_claim_scores:
        return 0.0
    return float(sum(per_claim_scores) / len(per_claim_scores))

