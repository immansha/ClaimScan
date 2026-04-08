from __future__ import annotations

from typing import Iterable, List, Set

from .base_grader import (
    ClaimGroundTruth,
    HARD_CONFIG,
    normalize_episode_scores,
    score_claim,
)
from models import Action


def _connected_fraud_customers(truths: List[ClaimGroundTruth]) -> Set[int]:
    """Indices of claims that should have F5 (connected fraud)."""

    indices: Set[int] = set()
    for idx, truth in enumerate(truths):
        if "F5" in truth.fraud_rules:
            indices.add(idx)
    return indices


def _all_connected_flagged(actions: List[Action], truths: List[ClaimGroundTruth]) -> bool:
    """Return True if all claims that should have F5 are correctly flagged with F5."""

    indices = _connected_fraud_customers(truths)
    if not indices:
        return False
    for idx in indices:
        if "F5" not in actions[idx].fraud_rules:
            return False
    return True


def grade_episode(actions: List[Action], truths: List[ClaimGroundTruth]) -> float:
    """Grade the hard task episode with connected fraud bonus."""

    all_connected_ok = _all_connected_flagged(actions, truths)
    scores: List[float] = []
    for idx, (action, truth) in enumerate(zip(actions, truths)):
        breakdown = score_claim(
            action,
            truth,
            config=HARD_CONFIG,
            connected_fraud_all_flagged=all_connected_ok,
        )
        scores.append(breakdown.total)
    return normalize_episode_scores(scores)

