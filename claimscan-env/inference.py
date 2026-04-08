from __future__ import annotations

import json
import os
from typing import Dict, Tuple

from dotenv import load_dotenv
from openai import OpenAI, OpenAIError, RateLimitError

from environment import ClaimScanEnv
from models import Action, Observation

# Load .env file if it exists
load_dotenv()


def _make_client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set.")
    base_url = os.getenv("API_BASE_URL")
    if base_url:
        return OpenAI(api_key=api_key, base_url=base_url)
    return OpenAI(api_key=api_key)


def _call_model(client: OpenAI, model: str, observation: Observation) -> Action:
    system_prompt = (
        "You are an insurance claims adjuster agent inside a deterministic benchmark.\n"
        "You MUST respond with a single JSON object with keys: "
        '"covered" (boolean), "payout" (number), "fraud_rules" (array of strings), '
        '"priority" (string one of P1,P2,P3,P4). No extra keys, no prose.\n'
        "Follow the coverage, payout, fraud, and priority rules exactly based on the observation."
    )

    user_content = json.dumps(observation.model_dump(), separators=(",", ":"))

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        temperature=0.0,
    )
    content = response.choices[0].message.content or ""

    # Best-effort strict JSON parsing with fallback to invalid action
    try:
        data = json.loads(content)
        return Action.model_validate(data)
    except Exception:
        # Invalid action format; environment will apply invalid-action penalty
        return Action(covered=False, payout=0.0, fraud_rules=[], priority="P4")


def _local_fallback_action(observation: Observation) -> Action:
    """Deterministic local fallback action when model calls are unavailable."""

    covered = observation.damage_type.lower() in {
        dmg.lower() for dmg in observation.covered_damages
    }
    payout = min(max(observation.claim_amount - observation.deductible, 0.0), observation.policy_limit)

    if observation.claim_amount > 10_000:
        priority = "P2"
    elif observation.claim_amount >= 1_000:
        priority = "P3"
    else:
        priority = "P4"

    return Action(covered=covered, payout=payout, fraud_rules=[], priority=priority)


def run_task(task_id: str, client: OpenAI, model_name: str) -> Tuple[float, int]:
    env = ClaimScanEnv()
    obs = env.reset(task_id=task_id, seed=42)
    total_reward = 0.0
    steps = 0

    print(f"[START] task={task_id}")

    done = False
    warned_fallback = False
    while not done:
        steps += 1
        print(f"[STEP] task={task_id} step={steps} observation_claim_id={obs.claim_id}")

        try:
            action = _call_model(client, model_name, obs)
        except RateLimitError as exc:
            if not warned_fallback:
                print(f"[WARN] task={task_id} using local fallback due to quota/rate limit: {exc}")
                warned_fallback = True
            action = _local_fallback_action(obs)
        except OpenAIError as exc:
            if not warned_fallback:
                print(f"[WARN] task={task_id} using local fallback due to OpenAI error: {exc}")
                warned_fallback = True
            action = _local_fallback_action(obs)

        next_obs, reward, done, info = env.step(action)
        total_reward += reward
        obs = next_obs if next_obs is not None else obs

    print(f"[END] task={task_id} total_reward={total_reward:.4f} steps={steps}")
    return total_reward, steps


def main() -> None:
    client = _make_client()
    model_name = os.getenv("MODEL_NAME", "gpt-4o")

    results: Dict[str, Dict[str, float | int]] = {}
    for task_id in ["easy", "medium", "hard"]:
        total_reward, steps = run_task(task_id, client, model_name)
        results[task_id] = {"total_reward": total_reward, "steps": steps}

    print(json.dumps({"results": results}, indent=2))


if __name__ == "__main__":
    main()

