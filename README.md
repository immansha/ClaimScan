---
title: claimscan-env
emoji: "🚑"
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# ClaimScan OpenEnv Benchmark

Deterministic insurance-claims benchmark environment for agent evaluation.

This repository contains the ClaimScan project under `claimscan-env/`.

## What This Project Includes

- FastAPI environment server (`/reset`, `/step`, `/state`, `/health`)
- Deterministic scoring and graders for easy/medium/hard tasks
- Local benchmark runner without OpenAI (`local_test.py`)
- OpenAI-backed runner (`inference.py`)
- Docker support for containerized deployment

## Repository Layout

```text
openenv/
  README.md
  QUICKSTART.md
  claimscan-env/
    environment.py
    inference.py
    local_test.py
    requirements.txt
    Dockerfile
    tasks/
    graders/
    tests/
```

## Quick Start (Windows)

### 1. Install dependencies

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe -m pip install -r requirements.txt
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe -m pip install pytest
```

### 2. Run API server

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe -m uvicorn environment:app --host 0.0.0.0 --port 7860
```

### 3. Validate API

```bat
curl http://127.0.0.1:7860/health
curl -X POST http://127.0.0.1:7860/reset -H "Content-Type: application/json" -d "{\"task_id\":\"easy\",\"seed\":42}"
```

### 4. Run tests

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe -m pytest tests
```

### 5. Run local benchmark (no API key needed)

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe local_test.py
```

## OpenAI Inference

1. Add your key to local environment (or `.env`) in `claimscan-env/`:

```env
OPENAI_API_KEY=your_key_here
MODEL_NAME=gpt-4o
```

2. Run inference:

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
C:\Users\imman\OneDrive\Desktop\openenv\.venv\Scripts\python.exe inference.py
```

If quota is unavailable, `inference.py` uses a deterministic local fallback so runs still complete.

## Docker

```bat
cd /d C:\Users\imman\OneDrive\Desktop\openenv\claimscan-env
docker build -t claimscan-env .
docker run -d --name claimscan-env-run -p 8001:7860 claimscan-env
curl http://127.0.0.1:8001/health
```

Stop and remove:

```bat
docker stop claimscan-env-run
docker rm claimscan-env-run
```

## Hugging Face Spaces (Docker)

1. Create a new Space with SDK: Docker.
2. Connect this GitHub repository.
3. Add Secrets:
   - `OPENAI_API_KEY`
   - `MODEL_NAME`
   - optional `API_BASE_URL`
4. Deploy and verify `/health`, `/reset`, and `/step`.

## Notes

- Do not commit `.env` or API keys.
- See `QUICKSTART.md` for an expanded local runbook.
