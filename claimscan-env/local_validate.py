from __future__ import annotations

from typing import Any, Dict, List

from fastapi.testclient import TestClient

from environment import app


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _reset(client: TestClient, task_id: str, seed: int = 42) -> Dict[str, Any]:
    resp = client.post("/reset", json={"task_id": task_id, "seed": seed})
    _assert(resp.status_code == 200, f"/reset failed for {task_id}: {resp.text}")
    payload = resp.json()
    _assert("claim_id" in payload, f"Missing claim_id in reset response for {task_id}")
    return payload


def _step(client: TestClient, action: Dict[str, Any]) -> Dict[str, Any]:
    resp = client.post("/step", json=action)
    _assert(resp.status_code == 200, f"/step failed: {resp.text}")
    payload = resp.json()
    _assert("reward" in payload and "done" in payload and "info" in payload, "Malformed /step response")
    return payload


def _grade(client: TestClient, task_id: str, actions: List[Dict[str, Any]]) -> Dict[str, Any]:
    resp = client.post("/grade", json={"task_id": task_id, "actions": actions})
    _assert(resp.status_code == 200, f"/grade failed for {task_id}: {resp.text}")
    payload = resp.json()
    _assert("score" in payload, f"Missing score in /grade response for {task_id}")
    return payload


def _perfect_action_for_observation(obs: Dict[str, Any], task_id: str) -> Dict[str, Any]:
    """
    Deterministic, environment-compatible action builder.
    It mirrors current task data intent with simple robust logic.
    """

    covered = obs["damage_type"] in set(obs["covered_damages"])
    payout = 0.0 if not covered else min(max(obs["claim_amount"] - obs["deductible"], 0.0), obs["policy_limit"])

    fraud_rules: List[str] = []
    # F1: filed within 7 days of policy start date (task truths currently rely on direct flags,
    # so this local validator keeps it simple and does not enforce all fraud derivations).
    if obs["past_claims_12m"] >= 3:
        fraud_rules.append("F2")
    if obs["claim_amount"] > 10000 and obs["tenure_days"] < 30:
        fraud_rules.append("F3")
    if obs["incident_date"] > obs["filing_date"]:
        fraud_rules.append("F4")
    if obs["claim_amount"] > 2 * obs["avg_amount_for_damage_type"]:
        fraud_rules.append("F6")
    if (
        obs["damage_type"] == "theft"
        and obs["claim_amount"] > 5000
        and "police_report" in obs["required_docs"]
        and "police_report" not in obs["docs_submitted"]
    ):
        fraud_rules.append("F7")

    # F5 appears in hard task for CUST-777 connected claims.
    if task_id == "hard" and obs["customer_id"] == "CUST-777":
        fraud_rules.append("F5")

    fraud_rules = sorted(set(fraud_rules))

    if fraud_rules and obs["claim_amount"] > 5000:
        priority = "P1"
    elif fraud_rules or obs["claim_amount"] > 10000:
        priority = "P2"
    elif 1000 <= obs["claim_amount"] <= 10000:
        priority = "P3"
    else:
        priority = "P4"

    return {
        "covered": covered,
        "payout": round(float(payout), 2),
        "fraud_rules": fraud_rules,
        "priority": priority,
    }


def validate_task(client: TestClient, task_id: str) -> float:
    obs = _reset(client, task_id)
    done = False
    actions: List[Dict[str, Any]] = []
    rewards: List[float] = []
    safety_counter = 0

    while not done:
        safety_counter += 1
        _assert(safety_counter <= 50, f"Potential infinite loop in task {task_id}")
        action = _perfect_action_for_observation(obs, task_id)
        actions.append(action)
        step_resp = _step(client, action)
        reward = float(step_resp["reward"])
        _assert(-1.0 <= reward <= 2.0, f"Invalid reward range for {task_id}: {reward}")
        rewards.append(reward)
        done = bool(step_resp["done"])
        if not done:
            obs = step_resp["observation"]

    grade_resp = _grade(client, task_id, actions)
    score = float(grade_resp["score"])
    _assert(0.0 <= score <= 1.0, f"Score out of [0,1] for {task_id}: {score}")
    return score


def validate_determinism(client: TestClient, task_id: str) -> None:
    first = validate_task(client, task_id)
    second = validate_task(client, task_id)
    _assert(abs(first - second) < 1e-12, f"Non-deterministic score for {task_id}: {first} vs {second}")


def main() -> None:
    client = TestClient(app)

    print("Running local ClaimScan validation...")
    scores: Dict[str, float] = {}
    for task_id in ("easy", "medium", "hard"):
        score = validate_task(client, task_id)
        scores[task_id] = score
        print(f"  - {task_id}: score={score:.4f}")

    for task_id in ("easy", "medium", "hard"):
        validate_determinism(client, task_id)
        print(f"  - {task_id}: determinism=ok")

    health = client.get("/health")
    _assert(health.status_code == 200, "/health failed")

    print("All local checks passed.")
    print(scores)


if __name__ == "__main__":
    main()

