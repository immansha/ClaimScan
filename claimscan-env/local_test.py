"""
Local benchmark test without OpenAI.
Tests the running FastAPI server directly with deterministic actions.
"""
from __future__ import annotations

import json
from typing import Dict

import httpx

from models import Action, Observation


BASE_URL = "http://127.0.0.1:7860"


def reset_task(task_id: str, seed: int = 42) -> Observation:
    """Reset a task and return the initial observation."""
    response = httpx.post(
        f"{BASE_URL}/reset",
        json={"task_id": task_id, "seed": seed},
        timeout=10.0,
    )
    response.raise_for_status()
    return Observation.model_validate(response.json())


def step_task(action: Action) -> tuple:
    """Step the environment with an action."""
    response = httpx.post(
        f"{BASE_URL}/step",
        json=action.model_dump(),
        timeout=10.0,
    )
    response.raise_for_status()
    data = response.json()
    obs = Observation.model_validate(data["observation"]) if data["observation"] else None
    reward = data["reward"]
    done = data["done"]
    info = data["info"]
    return obs, reward, done, info


def get_simple_action(obs: Observation) -> Action:
    """
    Deterministic action: always choose covered=True, payout=min(claim-deduct, limit), 
    no fraud rules, priority based on claim amount.
    """
    payout = min(max(obs.claim_amount - obs.deductible, 0), obs.policy_limit)
    
    # Deterministic priority: P1 if >10k, P2 if >5k, P3 if >1k, else P4
    if obs.claim_amount > 10_000:
        priority = "P1"
    elif obs.claim_amount > 5_000:
        priority = "P2"
    elif obs.claim_amount > 1_000:
        priority = "P3"
    else:
        priority = "P4"
    
    # Check if damage is covered (simplified)
    covered = obs.damage_type.lower() in [d.lower() for d in obs.covered_damages]
    
    return Action(covered=covered, payout=payout, fraud_rules=[], priority=priority)


def run_task_local(task_id: str) -> tuple:
    """Run a single task locally against the running server."""
    print(f"[START] task={task_id}")
    
    obs = reset_task(task_id)
    total_reward = 0.0
    steps = 0
    done = False
    
    while not done:
        steps += 1
        print(f"[STEP] task={task_id} step={steps} observation_claim_id={obs.claim_id}")
        
        action = get_simple_action(obs)
        next_obs, reward, done, info = step_task(action)
        total_reward += reward
        obs = next_obs if next_obs is not None else obs
    
    print(f"[END] task={task_id} total_reward={total_reward:.4f} steps={steps}")
    return total_reward, steps


def main() -> None:
    """Run all three tasks locally."""
    results: Dict[str, Dict[str, float | int]] = {}
    
    for task_id in ["easy", "medium", "hard"]:
        try:
            total_reward, steps = run_task_local(task_id)
            results[task_id] = {"total_reward": total_reward, "steps": steps}
        except Exception as e:
            print(f"[ERROR] task={task_id}: {e}")
            results[task_id] = {"error": str(e)}
    
    print("\n" + "=" * 60)
    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()
