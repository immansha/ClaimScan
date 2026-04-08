# ClaimScan Environmental Setup & Quickstart

## Project Structure
```
openenv/
├── claimscan-env/              # Main project folder
│   ├── environment.py          # FastAPI server
│   ├── models.py               # Data schemas (Action, Observation, etc.)
│   ├── inference.py            # OpenAI-powered benchmark runner
│   ├── local_test.py           # Local benchmark (no API key needed)
│   ├── coverage_rules.py       # Coverage logic
│   ├── fraud_rules.py          # Fraud detection rules
│   ├── priority_rules.py       # Priority assignment rules
│   ├── payout_calculator.py    # Payout formula
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Container config
│   ├── .env                    # API key config
│   ├── graders/                # Scoring logic
│   ├── tasks/                  # Benchmark tasks (easy/medium/hard)
│   └── tests/                  # Unit tests
└── .venv/                      # Virtual environment (already set up)
```

---

## Setup (One-time)

### 1. Navigate to project root
```cmd
cd C:\Users\imman\OneDrive\Desktop\openenv
```

### 2. Activate virtual environment (if not already active)
```cmd
.venv\Scripts\activate
```

### 3. Install dependencies
```cmd
pip install -r claimscan-env/requirements.txt
pip install pytest python-dotenv
```

---

## Running Everything

### Option A: Full Local Test (No API key needed) 
Runs all three tasks through the FastAPI server with deterministic actions:

```cmd
cd claimscan-env
python local_test.py
```

**Output:**
```
[START] task=easy
[STEP] task=easy step=1 observation_claim_id=E-001
[END] task=easy total_reward=1.1000 steps=1
[START] task=medium
[STEP] task=medium step=1 observation_claim_id=M-004
...
[END] task=medium total_reward=3.6000 steps=5
[START] task=hard
...
[END] task=hard total_reward=6.6000 steps=10
```

---

### Option B: Run Unit Tests 
```cmd
cd claimscan-env
python -m pytest tests -v
```

**Output:**
```
tests/test_grader.py::test_perfect_claim_scores_one PASSED
tests/test_grader.py::test_partial_claim_scores_fraction PASSED
tests/test_rules.py::test_damage_coverage_lists PASSED
tests/test_rules.py::test_priority_rules PASSED
```

---

### Option C: Run FastAPI Server Only
Starts the environment server on port 7860:

```cmd
cd claimscan-env
python -m uvicorn environment:app --host 0.0.0.0 --port 7860
```

Then in another terminal, test endpoints:
```powershell
# Check health
Invoke-WebRequest http://127.0.0.1:7860/health

# Reset easy task
$body = '{"task_id":"easy","seed":42}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:7860/reset -ContentType 'application/json' -Body $body

# Step through claim
$action = '{"covered":true,"payout":1500,"fraud_rules":[],"priority":"P3"}'
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:7860/step -ContentType 'application/json' -Body $action
```

View interactive docs at: http://127.0.0.1:7860/docs

---

### Option D: Run with OpenAI (GPT-4o inference) 
**Prerequisites:** Fix API quota at https://platform.openai.com/account/billing/overview

```cmd
cd claimscan-env
python inference.py
```

This runs GPT-4o on all three tasks and outputs final JSON scores.

---

### Option E: Build & Run Docker Container
**Prerequisites:** Docker Desktop running

```cmd
cd claimscan-env
docker build -t claimscan-env .
docker run -p 7860:7860 claimscan-env
```

Then access at: http://localhost:7860/health

---

## Complete End-to-End Run

Run all checks in order:

```cmd
# Navigate
cd C:\Users\imman\OneDrive\Desktop\openenv

# Activate env
.venv\Scripts\activate

# Run tests
cd claimscan-env
python -m pytest tests -v

# Run local benchmark
python local_test.py

# Start server (in background or new terminal)
python -m uvicorn environment:app --host 0.0.0.0 --port 7860
# Then in another terminal, run:
# python local_test.py (to verify server endpoints)
```

---

## Environment Variables (.env file)

Already set in `claimscan-env/.env`:
```
OPENAI_API_KEY=xxxxx.
MODEL_NAME=xxxxx
```

To update:
```cmd
notepad claimscan-env\.env
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `pip install -r claimscan-env/requirements.txt` |
| Port 7860 already in use | Kill process or use `--port 7861` |
| Docker connection error | Start Docker Desktop |
| OpenAI quota error | Update billing at api.openai.com/account/billing |
| Tests fail | Check imports with `python -m pytest tests -v` |

---

## Files You Modified

- `claimscan-env/.env` — Added API key
- `claimscan-env/inference.py` — Added `load_dotenv()` support
- `claimscan-env/*.py` — Fixed imports (from `.models` → from `models`)
- `claimscan-env/local_test.py` — Created local benchmark script

