from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from coverage_rules import damage_is_covered
from fraud_rules import FraudContext, evaluate_fraud_rules
from models import Action, Observation
from payout_calculator import calculate_payout
from priority_rules import calculate_priority
from tasks import load_easy_task, load_hard_task, load_medium_task


TaskId = str


@dataclass
class EpisodeState:
    task_id: TaskId
    claims: List[Dict[str, Any]]
    indices: List[int]
    current_index: int = 0
    steps_taken: int = 0
    max_steps: int = 0
    cumulative_reward: float = 0.0
    previous_reward: float = 0.0
    done: bool = False
    history_actions: List[Action] = field(default_factory=list)


TASK_CONFIG = {
    "easy": {"loader": load_easy_task, "max_steps": 5},
    "medium": {"loader": load_medium_task, "max_steps": 15},
    "hard": {"loader": load_hard_task, "max_steps": 30},
}


class ClaimScanEnv:
    """OpenEnv-compatible environment for insurance claim processing."""

    def __init__(self) -> None:
        self._state: Optional[EpisodeState] = None

    # OpenEnv interface
    def reset(self, task_id: str, seed: int | None = None) -> Observation:
        if task_id not in TASK_CONFIG:
            raise ValueError(f"Unknown task_id: {task_id}")

        config = TASK_CONFIG[task_id]
        claims = config["loader"]()
        num_claims = len(claims)

        rng = random.Random(seed)
        indices = list(range(num_claims))
        if seed is not None:
            rng.shuffle(indices)

        self._state = EpisodeState(
            task_id=task_id,
            claims=claims,
            indices=indices,
            max_steps=config["max_steps"],
        )

        return self._build_observation()

    def step(self, action: Action) -> Tuple[Optional[Observation], float, bool, Dict[str, Any]]:
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")

        state = self._state

        if state.done:
            # No further steps allowed after done
            return None, 0.0, True, {"error": "Episode already completed."}

        # Step counting and repeat-action penalty
        state.steps_taken += 1
        reward = 0.0
        info: Dict[str, Any] = {}

        # Validate max steps
        if state.steps_taken > state.max_steps:
            state.done = True
            info["reason"] = "max_steps_exceeded"
            return None, reward, True, info

        # Validate action format via Pydantic (already Action, but ensure deterministic handling)
        try:
            action = Action.model_validate(action)
        except ValidationError as exc:
            reward -= 0.1
            state.previous_reward = reward
            state.cumulative_reward += reward
            info["validation_error"] = json.loads(exc.json())
            return self._build_observation(), reward, False, info

        # Check for repeat action on same claim
        if state.history_actions and state.current_index < len(state.indices) and not state.done:
            if len(state.history_actions) > state.current_index:
                reward -= 0.05
                state.previous_reward = reward
                state.cumulative_reward += reward
                info["repeat_action"] = True
                return self._build_observation(), reward, False, info

        # Score against ground truth
        curr_idx = state.indices[state.current_index]
        claim_entry = state.claims[curr_idx]
        gt = claim_entry["ground_truth"]

        coverage_correct = 0.25 if bool(action.covered) == bool(gt["covered"]) else 0.0
        payout_correct = (
            0.25 if abs(action.payout - float(gt["payout"])) <= 0.01 else 0.0
        )
        fraud_correct = 0.25 if set(action.fraud_rules) == set(gt["fraud_rules"]) else 0.0
        priority_correct = 0.25 if action.priority == gt["priority"] else 0.0

        reward = coverage_correct + payout_correct + fraud_correct + priority_correct
        state.history_actions.append(action)

        # Move to next claim
        state.current_index += 1
        next_obs: Optional[Observation]
        done = state.current_index >= len(state.indices) or state.steps_taken >= state.max_steps
        state.done = done

        if done:
            next_obs = None
            if state.current_index >= len(state.indices) and state.steps_taken <= state.max_steps:
                reward += 0.1  # completion bonus
        else:
            next_obs = self._build_observation()

        state.previous_reward = reward
        state.cumulative_reward += reward

        info.update(
            {
                "coverage_correct": coverage_correct,
                "payout_correct": payout_correct,
                "fraud_rules_correct": fraud_correct,
                "priority_correct": priority_correct,
            }
        )

        return next_obs, reward, done, info

    def state(self) -> Dict[str, Any]:
        if self._state is None:
            raise RuntimeError("Environment not initialized. Call reset() first.")
        s = self._state
        return {
            "task_id": s.task_id,
            "current_index": s.current_index,
            "total_claims": len(s.indices),
            "steps_taken": s.steps_taken,
            "max_steps": s.max_steps,
            "cumulative_reward": s.cumulative_reward,
            "done": s.done,
        }

    # Internal helpers
    def _current_claim(self) -> Dict[str, Any]:
        assert self._state is not None
        state = self._state
        curr_idx = state.indices[state.current_index]
        return state.claims[curr_idx]["observation"]

    def _build_observation(self) -> Observation:
        assert self._state is not None
        state = self._state
        claim_obs = self._current_claim().copy()

        steps_remaining = max(state.max_steps - state.steps_taken, 0)
        claim_obs["steps_remaining"] = steps_remaining
        claim_obs["previous_reward"] = state.previous_reward

        return Observation.model_validate(claim_obs)


# FastAPI app exposing the environment
app = FastAPI(title="ClaimScan OpenEnv Environment", version="1.0.0")
_env = ClaimScanEnv()


class ResetRequest(BaseModel):
    task_id: str
    seed: Optional[int] = None


@app.post("/reset")
def api_reset(req: ResetRequest) -> Observation:
    try:
        return _env.reset(task_id=req.task_id, seed=req.seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/step")
def api_step(action: Action) -> Dict[str, Any]:
    try:
        obs, reward, done, info = _env.step(action)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "observation": obs.model_dump() if obs is not None else None,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/state")
def api_state() -> Dict[str, Any]:
    try:
        return _env.state()
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/health")
def api_health() -> Dict[str, str]:
    return {"status": "ok"}

