from __future__ import annotations

from importlib import resources
from typing import Any, Dict, List

import json


def _load_task_file(name: str) -> List[Dict[str, Any]]:
    """Load a task JSON file from the packaged resources."""

    with resources.files(__package__).joinpath(name).open("r", encoding="utf-8") as f:
        return json.load(f)


def load_easy_task() -> List[Dict[str, Any]]:
    return _load_task_file("easy_task.json")


def load_medium_task() -> List[Dict[str, Any]]:
    return _load_task_file("medium_task.json")


def load_hard_task() -> List[Dict[str, Any]]:
    return _load_task_file("hard_task.json")

