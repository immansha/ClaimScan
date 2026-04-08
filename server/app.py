"""Root server entrypoint required for multi-mode deployment checks."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn

# Ensure the environment module under `claimscan-env/` is importable from repo root.
REPO_ROOT = Path(__file__).resolve().parents[1]
CLAIMSCAN_DIR = REPO_ROOT / "claimscan-env"
if str(CLAIMSCAN_DIR) not in sys.path:
    sys.path.insert(0, str(CLAIMSCAN_DIR))

from environment import app  # noqa: E402


def main(host: str | None = None, port: int | None = None) -> None:
    """Callable server entrypoint expected by OpenEnv validator."""
    host = host or os.getenv("HOST", "0.0.0.0")
    port = port or int(os.getenv("PORT", "7860"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
