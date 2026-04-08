from __future__ import annotations

from typing import List

from models import PolicyType


AUTO_COVERED_DAMAGES: List[str] = [
    "collision",
    "weather",
    "theft",
    "fire",
    "vandalism",
    "glass",
]

HOME_COVERED_DAMAGES: List[str] = [
    "fire",
    "storm",
    "theft",
    "vandalism",
    "water_damage",
    "lightning",
]

HEALTH_COVERED_DAMAGES: List[str] = [
    "accident",
    "illness",
    "surgery",
    "emergency",
    "prescription",
]


def get_policy_limit(policy_type: PolicyType) -> float:
    """Return the hard-coded policy limit for the policy type."""

    if policy_type == "auto":
        return 50_000.0
    if policy_type == "home":
        return 200_000.0
    if policy_type == "health":
        return 1_000_000.0
    # This should never occur if PolicyType is enforced, but keep a clear error.
    raise ValueError(f"Unsupported policy type: {policy_type}")


def damage_is_covered(policy_type: PolicyType, damage_type: str) -> bool:
    """Return True if the given damage_type is covered by the policy type."""

    damage_type = damage_type.lower()
    if policy_type == "auto":
        return damage_type in AUTO_COVERED_DAMAGES
    if policy_type == "home":
        return damage_type in HOME_COVERED_DAMAGES
    if policy_type == "health":
        return damage_type in HEALTH_COVERED_DAMAGES
    return False


def covered_damages_for_policy(policy_type: PolicyType) -> List[str]:
    """Return the canonical list of covered damages for a policy type."""

    if policy_type == "auto":
        return list(AUTO_COVERED_DAMAGES)
    if policy_type == "home":
        return list(HOME_COVERED_DAMAGES)
    if policy_type == "health":
        return list(HEALTH_COVERED_DAMAGES)
    raise ValueError(f"Unsupported policy type: {policy_type}")

