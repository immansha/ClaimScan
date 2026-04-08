from __future__ import annotations

from coverage_rules import damage_is_covered
from priority_rules import calculate_priority


def test_damage_coverage_lists():
    assert damage_is_covered("auto", "collision")
    assert not damage_is_covered("auto", "storm")
    assert damage_is_covered("home", "storm")
    assert not damage_is_covered("home", "glass")


def test_priority_rules():
    assert calculate_priority(6000, ["F1"]) == "P1"
    assert calculate_priority(11_000, []) == "P2"
    assert calculate_priority(5000, []) == "P3"
    assert calculate_priority(500, []) == "P4"

