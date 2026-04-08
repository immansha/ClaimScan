## ClaimScan: Deterministic Insurance Claims Benchmark

ClaimScan is an OpenEnv-compatible benchmark where an AI agent acts as an insurance claims adjuster. The agent receives structured insurance claim observations and must decide **coverage**, compute the **payout**, detect **fraud rules**, and assign a **priority** level. All scoring is fully deterministic with no subjective components or embedded LLMs.

### 1. Environment motivation

- **Insurance claims** are a natural fit for agents: they require deterministic business rules, arithmetic, and cross-claim reasoning (connected fraud).
- **ClaimScan** isolates these skills into a compact benchmark with three tasks (easy/medium/hard) and explicit reward shaping.
- The environment is designed to be **production-ready**, **deterministic**, and deployable to **Hugging Face Spaces**.

### 2. Action space

The agent must output the following JSON action at each step:

```json
{
  "covered": true,
  "payout": 11500,
  "fraud_rules": ["F1", "F3"],
  "priority": "P2"
}
```

- **covered**: boolean – whether the damage type is covered under the policy.
- **payout**: float – computed according to the payout formula and capped by policy limit.
- **fraud_rules**: string[] – list of fraud rule identifiers (subset of `["F1", ..., "F7"]`).
- **priority**: `"P1" | "P2" | "P3" | "P4"` – claim handling priority.

### 3. Observation space

Each step exposes a structured JSON observation:

- **claim_id**: unique ID for the claim within the episode.
- **customer_id**: stable identifier for the customer (used for connected fraud F5).
- **tenure_days**: integer days since policy start for this customer.
- **past_claims_12m**: integer count of claims filed in the last 12 months.
- **policy_type**: `"auto" | "home" | "health"`.
- **policy_limit**: numeric policy limit for the claim.
- **policy_start_date**: ISO date string `"YYYY-MM-DD"`.
- **covered_damages**: list of damage types covered by this policy instance.
- **damage_type**: specific damage type for this claim.
- **incident_date**: ISO date of incident.
- **filing_date**: ISO date the claim was filed.
- **claim_amount**: claimed amount in dollars.
- **deductible**: deductible in dollars.
- **required_docs**: list of required document types for this claim.
- **docs_submitted**: list of documents actually submitted.
- **avg_amount_for_damage_type**: historical average amount for this damage type.
- **queue_position**: 1-based position in the episode’s claim queue.
- **queue_length**: total number of claims in the episode.
- **steps_remaining**: remaining step budget for the episode.
- **previous_reward**: reward obtained on the previous step (0.0 for the first step).

### 4. Fraud rules (F1–F7)

The only fraud logic in the environment is implemented in `fraud_rules.py`:

- **F1**: Filed within 7 days of policy start date  
  `filing_date - policy_start_date <= 7 days`
- **F2**: Customer has 3+ claims in last 12 months  
  `past_claims_12m >= 3`
- **F3**: Claim amount > $10,000 **and** tenure < 30 days  
  `claim_amount > 10000 and tenure_days < 30`
- **F4**: Incident date is after filing date (future-dated incident)  
  `incident_date > filing_date`
- **F5**: Same `customer_id` appears in 2+ claims in the current episode queue.
- **F6**: Claim amount > 2x average for this damage type  
  `claim_amount > 2 * avg_amount_for_damage_type`
- **F7**: Missing required police report for theft > $5,000  
  `damage_type == "theft" and claim_amount > 5000 and "police_report" required but not submitted`

### 5. Priority rules (P1–P4)

Implemented in `priority_rules.py`:

- **P1**: Any fraud rule triggered **and** claim amount > $5,000.
- **P2**: Any fraud rule triggered **or** claim amount > $10,000.
- **P3**: No fraud rules, claim amount in \[1,000, 10,000\].
- **P4**: No fraud rules, claim amount < 1,000 (or any remaining cases).

### 6. Coverage rules

Policy coverage is implemented in `coverage_rules.py`:

- **Auto policy covers**: `collision`, `weather`, `theft`, `fire`, `vandalism`, `glass`
- **Home policy covers**: `fire`, `storm`, `theft`, `vandalism`, `water_damage`, `lightning`
- **Health policy covers**: `accident`, `illness`, `surgery`, `emergency`, `prescription`

Anything not in the respective list is **not covered**.

### 7. Payout formula

The payout is computed in `payout_calculator.py`:

`payout = min(max(claim_amount - deductible, 0), policy_limit)`

Canonical policy limits:

- **Auto**: 50,000
- **Home**: 200,000
- **Health**: 1,000,000

### 8. Tasks

Defined under `tasks/` as JSON.

- **Easy** (`easy_task.json`)  
  - 1 auto claim, weather damage (hail), honest customer.  
  - Claim: \$2,000, deductible \$500 → payout 1,500.  
  - Expected: `covered=true`, `payout=1500`, `fraud_rules=[]`, `priority="P3"`.

- **Medium** (`medium_task.json`) – 5 claims  
  - Claims 1–3: deterministic fraud rules **F1**, **F2**, **F3** respectively.  
  - Claims 4–5: honest claims with no fraud.

- **Hard** (`hard_task.json`) – 10 claims  
  - Claims 1–3: same `customer_id = "CUST-777"` → **F5** on all three.  
  - Claim 4: **F4** (incident date after filing).  
  - Claim 5: **F6** (amount > 2x damage-type average).  
  - Claim 6: **F7** (theft > \$5,000 with missing police report).  
  - Claims 7–10: mix of honest and other fraud patterns (e.g. F2).

### 9. Grading and rewards

Per-claim reward (easy/medium tasks, and environment’s internal step rewards):

- **Coverage correct**: +0.25
- **Payout exact** (within \$0.01): +0.25
- **Fraud rules set matches exactly**: +0.25
- **Priority matches**: +0.25

For the **hard task** graders:

- Each component: +0.20 (coverage, payout, fraud, priority).  
- **Connected fraud bonus**: +0.15 if **all** claims that should have `F5` are correctly flagged with `F5`.

Environment rewards:

- Perfect claim (all four components correct): up to **+1.0**.  
- Partial claims: sum of component weights only.  
- Invalid action format: **-0.10**.  
- Repeating an action on the same claim: **-0.05**.  
- Episode completion bonus: **+0.10** if all claims processed within step budget.

### 10. Setup and running

#### Local (Python)

```bash
cd claimscan-env
pip install -r requirements.txt

# Run FastAPI environment server
uvicorn environment:app --host 0.0.0.0 --port 7860
```

API endpoints:

- `POST /reset` – body `{"task_id": "easy" | "medium" | "hard", "seed": 42}`  
- `POST /step` – body is the **Action** JSON.  
- `GET /state` – current environment state.  
- `GET /health` – simple health check.

#### Docker

```bash
cd claimscan-env
docker build -t claimscan-env .
docker run -p 7860:7860 claimscan-env
```

The FastAPI app will be available at `http://localhost:7860`.

### 11. Baseline evaluation (inference.py)

`inference.py` runs a simple baseline using OpenAI models:

```bash
export OPENAI_API_KEY=...
export MODEL_NAME=gpt-4o
python -m claimscan_env.inference
```

It logs with the required markers:

- `[START] task=...`
- `[STEP] task=... step=... observation_claim_id=...`
- `[END] task=... total_reward=... steps=...`

#### Expected baseline scores

These are approximate reference values (not enforced in code):

- **GPT-4o**  
  - Easy: ~0.98  
  - Medium: ~0.85  
  - Hard: ~0.65
- **GPT-3.5**  
  - Easy: ~0.95  
  - Medium: ~0.70  
  - Hard: ~0.45

### 12. Example claim and correct response

Example observation (simplified):

```json
{
  "claim_id": "C-001",
  "customer_id": "CUST-777",
  "tenure_days": 45,
  "past_claims_12m": 2,
  "policy_type": "auto",
  "policy_limit": 50000,
  "policy_start_date": "2026-02-24",
  "covered_damages": ["collision", "weather", "theft", "fire", "vandalism", "glass"],
  "damage_type": "theft",
  "incident_date": "2026-04-05",
  "filing_date": "2026-04-10",
  "claim_amount": 12000,
  "deductible": 500,
  "required_docs": ["police_report"],
  "docs_submitted": ["police_report", "photos"],
  "avg_amount_for_damage_type": 2500,
  "queue_position": 1,
  "queue_length": 5,
  "steps_remaining": 12,
  "previous_reward": 0.75
}
``+

Correct action:

```json
{
  "covered": true,
  "payout": 11500,
  "fraud_rules": [],
  "priority": "P2"
}
```

### 13. Validation checklist

- `openenv validate` passes with `openenv.yaml`.  
- `docker build` and `docker run` complete without errors (FastAPI server starts on port 7860).  
- `inference.py` runs within typical time budgets (< 20 minutes on standard hardware).  
- All graders (`easy_grader.py`, `medium_grader.py`, `hard_grader.py`) return scores in \[0.0, 1.0\] and are fully deterministic.  
- Episode step limits are respected; no infinite loops.  
- Rewards are only issued on claim completion (plus format/duplicate-action penalties) and are deterministic for a given action sequence.

