---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: apache-2.0
tags:
  - openenv
  - email-triage
  - ai-agent
  - reinforcement-learning
  - fastapi
  - openai
  - meta
  - pytorch
short_description: AI email triage environment for the Meta + PyTorch OpenEnv Hackathon
---

# Email Triage OpenEnv

An AI email triage environment built on the **OpenEnv specification** for the **Meta + PyTorch OpenEnv Hackathon**. Simulates a real-world customer support workflow where an AI agent reads incoming emails, classifies their category, assigns priority, and drafts a professional reply — evaluated by automated graders across 3 progressive tasks.

Uses the **OpenAI client** for all LLM calls — supports GPT-4o-mini (via OpenAI API) or Meta Llama 3.1 8B (via HuggingFace router).

---

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run baseline inference (rule-based fallback, no token needed)
python inference.py

# 3. Run with LLM — Option A: OpenAI (GPT-4o-mini)
OPENAI_API_KEY=sk-... python inference.py

# 4. Run with LLM — Option B: HuggingFace (Llama 3.1 8B)
HF_TOKEN=hf_... python inference.py

# 5. Start the full backend server
OPENAI_API_KEY=sk-... uvicorn backend.main:app --host 0.0.0.0 --port 7860
```

---

## Environment Overview

| Property | Value |
|---|---|
| Observation | email_id, subject, body, sender, history |
| Action | category, priority, reply |
| Reward range | 0.0 – 1.0 |
| Tasks | 3 (Easy → Medium → Hard) |
| Dataset | 25 real-world support emails |
| Runtime | < 5 minutes on 2 vCPU / 8 GB RAM |

---

## OpenEnv API

| Endpoint | Method | Description |
|---|---|---|
| `/api/reset` | POST | Reset environment, load next email. Query param: `?email_id=` |
| `/api/step` | POST | Submit triage action, receive reward |
| `/api/state` | GET | Current environment state + score history |
| `/api/health` | GET | Health check |
| `/api/tasks` | GET | List all 3 tasks |
| `/api/emails` | GET | List all emails (filter by category/priority) |
| `/api/triage` | POST | Triage any arbitrary email via LLM (no ground truth needed) |
| `/api/agent/status` | GET | LLM agent status (model, provider, ready) |

### Observation (reset response)
```json
{
  "email_id": "email_001",
  "subject": "Cannot login to my account",
  "body": "I have been locked out...",
  "sender": "user@example.com",
  "history": []
}
```

### Action (step request)
```json
{
  "category": "Account",
  "priority": "High",
  "reply": "We sincerely apologize for the inconvenience..."
}
```

### Reward (step response)
```json
{
  "score": 1.0,
  "explanation": "Category correct. Priority correct. Reply quality: 1.00.",
  "breakdown": {
    "category": {"score": 1.0, "predicted": "Account", "expected": "Account"},
    "priority":  {"score": 1.0, "predicted": "High",    "expected": "High"},
    "reply":     {"score": 1.0, "detail": {"apology_present": true, "solution_provided": true, "professional_tone": true, "addresses_subject": true}}
  }
}
```

---

## Reward Formula

```
reward = 0.5 × category_correct
       + 0.3 × priority_correct
       + 0.2 × reply_quality

penalties:
  invalid_action: -0.2
  empty_reply:    -0.1
```

---

## Tasks

### Task 1 — Email Classification (Easy, weight: 0.5)
Classify the email into one of 4 categories:
- **Billing Refund** — refunds, duplicate charges, invoices, billing errors
- **Account** — login failures, password reset, 2FA, locked accounts, profile updates
- **Feature Request** — suggestions, integrations, UI improvements
- **Technical Support** — bugs, crashes, server errors, timeouts

Grader: `EasyGrader` — binary 1.0 / 0.0

### Task 2 — Priority Detection (Medium, weight: 0.3)
Assign urgency level: **Low / Medium / High**

Grader: `MediumGrader` — partial credit for adjacent levels (1.0 / 0.5 / 0.0)

### Task 3 — Reply Generation (Hard, weight: 0.2)
Draft a professional customer support reply.

Grader: `HardGrader` — 4 checks, each worth 0.25:
1. Apology/acknowledgment present
2. Solution or next step provided
3. Professional tone (no slang, formal closing)
4. Addresses keywords from the email subject

---

## Inference Script Log Format

The `inference.py` script emits structured logs required by the OpenEnv spec:

```
[START] {"event": "start", "model": "gpt-4o-mini", "provider": "openai", "mode": "openai", ...}

[STEP] {"event": "step", "step": 1, "email_id": "email_001", "action": {...}, "reward": {...}, "expected": {...}}
[STEP] {"event": "step", "step": 2, ...}
...

[END] {"event": "end", "model": "gpt-4o-mini", "total_emails": 25, "average_score": 0.994, "category_accuracy": 1.0, "priority_accuracy": 0.96, ...}
```

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | No* | — | OpenAI API key. Enables GPT-4o-mini. Takes priority over HF_TOKEN. |
| `HF_TOKEN` | No* | — | HuggingFace token. Enables Llama 3.1 8B via HF router. |
| `API_BASE_URL` | No | `https://router.huggingface.co/v1` | LLM API base URL. Ignored when OPENAI_API_KEY is set. |
| `MODEL_NAME` | No | `gpt-4o-mini` / `meta-llama/Llama-3.1-8B-Instruct` | LLM model ID. |

*At least one of `OPENAI_API_KEY` or `HF_TOKEN` is needed for real LLM inference. Without either, falls back to rule-based triage.

---

## LLM Integration

Uses the **OpenAI client** for all LLM calls (hackathon requirement):

```python
from openai import OpenAI

# Option A: OpenAI direct
client = OpenAI(api_key=OPENAI_API_KEY)

# Option B: HuggingFace router (OpenAI-compatible)
client = OpenAI(
    base_url="https://router.huggingface.co/v1",
    api_key=HF_TOKEN,
)

response = client.chat.completions.create(
    model="gpt-4o-mini",   # or "meta-llama/Llama-3.1-8B-Instruct"
    messages=[
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": email_content},
    ],
    max_tokens=600,
    temperature=0.1,
    response_format={"type": "json_object"},
)
```

---

## Baseline Results (GPT-4o-mini)

| Metric | Score |
|---|---|
| Category Accuracy | 25/25 — **100%** |
| Priority Accuracy | 24/25 — **96%** |
| Average Score | **0.994 / 1.0** |
| Pass Rate | 25/25 — **100%** |

---

## HuggingFace Spaces Deployment

```bash
# Build and run locally with Docker
docker build -t email-triage-openenv .
docker run -p 7860:7860 -e OPENAI_API_KEY=sk-... email-triage-openenv

# Verify
curl http://localhost:7860/api/health
curl -X POST http://localhost:7860/api/reset
```

The app runs on **port 7860** (required by HF Spaces) as a non-root user (UID 1000).

To deploy on HF Spaces:
1. Create a new Space → Docker SDK
2. Push this repository
3. Set `OPENAI_API_KEY` (or `HF_TOKEN`) in Space secrets

---

## Project Structure

```
email_traiga_openenv/
├── backend/
│   ├── main.py                  # FastAPI app entry point
│   ├── models.py                # Pydantic typed models (Observation, Action, Reward)
│   ├── api/routes.py            # All API endpoints
│   ├── env/
│   │   └── email_triage_env.py  # OpenEnv environment class
│   ├── graders/
│   │   ├── easy_grader.py       # Task 1: binary category match
│   │   ├── medium_grader.py     # Task 2: priority with partial credit
│   │   └── hard_grader.py       # Task 3: reply quality (4 checks)
│   ├── ai/
│   │   └── hf_agent.py          # OpenAI client (OpenAI or HF router)
│   └── data/emails.json         # 25 support emails dataset
├── frontend/                    # React + Vite + TailwindCSS dashboard
├── inference.py                 # Baseline agent script (OpenEnv spec)
├── openenv.yaml                 # Environment specification
├── Dockerfile                   # HF Spaces-compatible multi-stage build
└── requirements.txt
```

---

## Hackathon Compliance Checklist

- [x] Real-world task (email triage — not a game/toy)
- [x] Full OpenEnv spec: `POST /api/reset`, `POST /api/step`, `GET /api/state`
- [x] Typed observation, action, reward models (Pydantic)
- [x] 3 tasks with progressive difficulty (Easy → Medium → Hard)
- [x] Reward 0.0–1.0 with partial progress signals (partial credit on priority)
- [x] `inference.py` in project root with `[START]` / `[STEP]` / `[END]` markers on same line as JSON
- [x] Uses OpenAI client for all LLM calls (direct or via HF router)
- [x] Required env vars: `HF_TOKEN`, `API_BASE_URL`, `MODEL_NAME`
- [x] Dockerfile for HuggingFace Spaces (port 7860, non-root UID 1000)
- [x] Runtime < 20 minutes on 2 vCPU / 8 GB RAM
- [x] `openenv.yaml` environment specification
- [x] Dataset: 25 diverse real-world support emails
