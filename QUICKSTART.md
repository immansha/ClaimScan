ClaimScan Environmental Setup & Quickstart
Project Structure
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
│   ├── .env                    # API key config (ignored in git)
│   ├── graders/                # Scoring logic
│   ├── tasks/                  # Benchmark tasks (easy/medium/hard)
│   └── tests/                  # Unit tests
└── .venv/                      # Virtual environment (optional)
Setup (One-time)
1. Navigate to project root
cd openenv
2. Activate virtual environment (if not already active)
# Windows
.venv\Scripts\activate

# macOS / Linux
source .venv/bin/activate
3. Install dependencies
pip install -r claimscan-env/requirements.txt
pip install pytest python-dotenv
Running the Project
Option A: Full Local Test (No API key needed) 

Runs all three tasks with deterministic actions:

cd claimscan-env
python local_test.py

Sample Output:

[START] task=easy
[STEP] task=easy step=1 observation_claim_id=E-001
[END] task=easy total_reward=1.1000 steps=1
[START] task=medium
[STEP] task=medium step=1 observation_claim_id=M-004
[END] task=medium total_reward=3.6000 steps=5
[START] task=hard
...
[END] task=hard total_reward=6.6000 steps=10

Option B: Run Unit Tests 
cd claimscan-env
python -m pytest tests -v

Sample Output:

tests/test_grader.py::test_perfect_claim_scores_one PASSED
tests/test_grader.py::test_partial_claim_scores_fraction PASSED
tests/test_rules.py::test_damage_coverage_lists PASSED
tests/test_rules.py::test_priority_rules PASSED

Option C: Run FastAPI Server Only

Starts the environment server on port 7860:

cd claimscan-env
python -m uvicorn environment:app --host 0.0.0.0 --port 7860

Test endpoints in another terminal:

# Check health
curl http://127.0.0.1:7860/health

# Reset easy task
curl -X POST http://127.0.0.1:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id":"easy","seed":42}'

# Step through claim
curl -X POST http://127.0.0.1:7860/step \
  -H "Content-Type: application/json" \
  -d '{"covered":true,"payout":1500,"fraud_rules":[],"priority":"P3"}'

View interactive docs at: http://127.0.0.1:7860/docs

Option D: Run with OpenAI (GPT-4o inference)

Prerequisites: Add your API key to .env

cd claimscan-env
python inference.py

This runs GPT-4o on all tasks and outputs JSON scores.

Option E: Build & Run Docker Container

Prerequisites: Docker installed and running

cd claimscan-env
docker build -t claimscan-env .
docker run -p 7860:7860 claimscan-env

Access at: http://localhost:7860/health

Complete End-to-End Run
# Navigate
cd openenv

# Activate env
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

# Run tests
cd claimscan-env
python -m pytest tests -v

# Run local benchmark
python local_test.py

# Start server
python -m uvicorn environment:app --host 0.0.0.0 --port 7860
# Then verify endpoints
python local_test.py
Environment Variables (.env file)

Create claimscan-env/.env and set your keys:

OPENAI_API_KEY=YOUR_OPENAI_API_KEY
MODEL_NAME=gpt-4o
Troubleshooting
Issue	Solution
ModuleNotFoundError	Run pip install -r claimscan-env/requirements.txt
Port 7860 already in use	Kill process or change port with --port 7861
Docker connection error	Start Docker Desktop
OpenAI quota error	Update billing at OpenAI

Tests fail	Check imports with python -m pytest tests -v
