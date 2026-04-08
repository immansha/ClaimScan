from __future__ import annotations

from typing import List

from .base_grader import ClaimGroundTruth, DEFAULT_CONFIG, normalize_episode_scores, score_claim
from models import Action


def grade_episode(actions: List[Action], truths: List[ClaimGroundTruth]) -> float:
    """Grade the easy task episode and return a deterministic score in [0, 1]."""

    scores: List[float] = []
    for action, truth in zip(actions, truths):
        breakdown = score_claim(action, truth, config=DEFAULT_CONFIG)
        scores.append(breakdown.total)
    return normalize_episode_scores(scores)

