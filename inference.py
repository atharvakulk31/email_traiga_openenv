"""
inference.py — Baseline Agent Script for Email Triage OpenEnv
=============================================================

Self-contained: imports the environment directly (no running server needed).
Uses OpenAI client with HuggingFace router for LLM inference.
Falls back to rule-based keyword matching if HF_TOKEN is not set.

Required log markers (OpenEnv spec):
  [START]  — emitted once at the start
  [STEP]   — emitted once per email
  [END]    — emitted once with aggregate results

Environment variables:
  HF_TOKEN      — HuggingFace token (required for LLM inference)
  API_BASE_URL  — LLM API base URL (default: https://router.huggingface.co/v1)
  MODEL_NAME    — model ID  (default: meta-llama/Llama-3.1-8B-Instruct)

Usage:
  # Rule-based (no token):
  python inference.py

  # Full LLM:
  HF_TOKEN=hf_... python inference.py

  # Custom model/endpoint:
  HF_TOKEN=hf_... MODEL_NAME=Qwen/Qwen2.5-7B-Instruct python inference.py
"""

import os
import sys
import json
import re
import time

# ── Environment variables ──────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
HF_TOKEN       = os.getenv("HF_TOKEN",       "")
MODEL_NAME     = os.getenv("MODEL_NAME",     "gpt-4o-mini" if OPENAI_API_KEY else "meta-llama/Llama-3.1-8B-Instruct")
# OpenAI takes priority; fallback to HuggingFace router
API_KEY        = OPENAI_API_KEY or HF_TOKEN
API_BASE_URL   = None if OPENAI_API_KEY else os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")

# ── Import env + graders directly (self-contained) ────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))

from backend.env.email_triage_env import EmailTriageEnv
from backend.graders.easy_grader   import EasyGrader
from backend.graders.medium_grader import MediumGrader
from backend.graders.hard_grader   import HardGrader
from backend.models                import Action

VALID_CATEGORIES = ["Billing Refund", "Account", "Feature Request", "Technical Support"]
VALID_PRIORITIES = ["Low", "Medium", "High"]

SYSTEM_PROMPT = """You are an expert customer support triage agent for a SaaS company.

Analyze the email and respond with ONLY a valid JSON object — no markdown, no explanation:

{
  "category": "<Billing Refund | Account | Feature Request | Technical Support>",
  "priority": "<Low | Medium | High>",
  "reply": "<professional customer support reply>"
}

=== CATEGORY RULES ===
- Billing Refund: refunds, duplicate/wrong charges, unauthorized transactions, invoices, pricing inquiries, discount requests, subscription changes, billing address changes
- Account: login failures, password reset, 2FA problems, locked accounts, profile updates, email address changes, access issues — changes requiring support team action on account settings
- Feature Request: suggestions for NEW features, integrations, UI improvements — things the user wants ADDED that don't yet exist
- Technical Support: bugs, crashes, server errors (4xx/5xx), timeouts, blank screens, broken functionality, email deliverability issues, export failures

=== PRIORITY RULES ===
High — explicit urgency OR severe financial/access impact:
  • Hard deadline stated: "demo in X hours", "report due tomorrow", "payroll today", "audit tomorrow"
  • Explicit words: "urgent", "ASAP", "immediately", "critical", "emergency", "cannot access at all"
  • Complete access loss: account locked out, password reset broken, 2FA failing (cannot log in at all)
  • Unauthorized financial harm: charged after cancellation, duplicate charges, wrong plan billed
  • Physical product damage requiring refund
  • System-wide outages: server errors affecting all users, dashboard blank for entire team

Medium — active problem, no hard deadline:
  • Bugs reducing productivity but user can still partially work
  • Invoice discrepancy or billing error that needs correction (no emergency)
  • API rate limits causing pipeline failures (actively blocking work, not a feature request)
  • Routine account changes that require support team action: email address update, billing address change
  • Technical issue affecting one user with no stated time pressure
  • Notification deliverability issues (missing important updates)

Low — non-blocking, no urgency, aspirational:
  • ALL feature suggestions and enhancement requests (no matter how useful)
  • Bulk/enterprise pricing inquiries with no urgency
  • Subscription plan change requests (monthly to annual) with no stated deadline
  • General questions with no impact on current work

=== REPLY RULES — ALL 4 ARE GRADED ===
1. APOLOGY/EMPATHY (mandatory — every reply must include at least one):
   Use: "We sincerely apologize", "We're sorry to hear", "We apologize for the inconvenience",
        "We understand your frustration", "We're sorry for the trouble", "We understand this is frustrating"
   For feature requests use: "Thank you for this suggestion. We sincerely apologize this feature isn't available yet."

2. SOLUTION/NEXT STEP (mandatory):
   Provide a concrete action: will investigate, will process refund, escalating to team, steps to follow

3. PROFESSIONAL TONE (mandatory):
   Formal language only. No slang. Proper grammar. End with exactly: "Best regards, Support Team"

4. ADDRESS THE SUBJECT (mandatory):
   Use specific keywords from the email subject in your reply body.
   e.g. if subject is "Login Page Returning 500 Error" — mention "login page" and "500 error" in reply.

Length: 3-5 sentences. Be specific, not generic."""


# ── LLM agent (OpenAI client) ─────────────────────────────────────────────────

def llm_triage(subject: str, body: str, sender: str) -> dict:
    """Call LLM via OpenAI client (OpenAI or HuggingFace router)."""
    from openai import OpenAI

    kwargs = {"api_key": API_KEY}
    if API_BASE_URL:
        kwargs["base_url"] = API_BASE_URL
    client = OpenAI(**kwargs)

    user_msg = f"Subject: {subject}\nFrom: {sender}\n\n{body[:2000]}"

    create_kwargs = dict(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": user_msg},
        ],
        max_tokens=600,
        temperature=0.1,
    )
    # JSON mode only supported by OpenAI — HuggingFace router ignores it or errors
    if OPENAI_API_KEY:
        create_kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**create_kwargs)

    content = response.choices[0].message.content.strip()
    content = re.sub(r"```(?:json)?\s*", "", content).strip("` \n")
    match   = re.search(r"\{.*\}", content, re.DOTALL)
    if match:
        content = match.group(0)

    data = json.loads(content)

    category = data.get("category", "Technical Support")
    if category not in VALID_CATEGORIES:
        category = next(
            (c for c in VALID_CATEGORIES if c.lower() in category.lower()),
            "Technical Support"
        )

    priority = data.get("priority", "Medium").capitalize()
    if priority not in VALID_PRIORITIES:
        priority = "Medium"

    return {
        "category": category,
        "priority": priority,
        "reply":    data.get("reply", "").strip(),
    }


# ── Rule-based fallback ───────────────────────────────────────────────────────

def rule_based_triage(subject: str, body: str) -> dict:
    """Keyword-based triage — used when HF_TOKEN is not set."""
    text = f"{subject} {body}".lower()

    category = "Technical Support"
    if any(w in text for w in ["refund", "charge", "billing", "invoice",
                                "payment", "price", "cost", "discount"]):
        category = "Billing Refund"
    elif any(w in text for w in ["account", "login", "password", "reset",
                                  "2fa", "two-factor", "access", "profile", "locked"]):
        category = "Account"
    elif any(w in text for w in ["feature", "suggest", "request", "idea",
                                  "integration", "export", "dark mode", "slack"]):
        category = "Feature Request"

    priority = "Medium"
    if any(w in text for w in ["urgent", "asap", "immediately", "critical",
                                "crash", "locked out", "charged twice", "deadline"]):
        priority = "High"
    elif any(w in text for w in ["suggestion", "idea", "would be nice", "minor"]):
        priority = "Low"

    reply = (
        f"Dear Customer,\n\n"
        f"Thank you for contacting us. We sincerely apologize for the inconvenience "
        f"regarding \"{subject}\". Our support team will investigate and provide a "
        f"resolution within 24 hours.\n\n"
        f"Best regards,\nSupport Team"
    )
    return {"category": category, "priority": priority, "reply": reply}


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    use_llm  = bool(API_KEY)
    provider = "openai" if OPENAI_API_KEY else ("huggingface" if HF_TOKEN else "rule-based")
    mode     = provider if use_llm else "rule-based"
    model    = MODEL_NAME if use_llm else "rule-based"

    # ── [START] ───────────────────────────────────────────────────────────────
    start_log = json.dumps({
        "event":       "start",
        "model":       model,
        "provider":    provider,
        "mode":        mode,
        "description": "Email Triage OpenEnv — classifies, prioritises and replies to support emails",
    })
    print(f"[START] {start_log}", flush=True)

    # Initialise environment and graders directly
    env = EmailTriageEnv()
    emails = env.get_all_emails()
    print(f"[INFO] Loaded {len(emails)} emails from dataset", flush=True)
    print(f"[INFO] Tasks: EasyGrader(cat) | MediumGrader(pri) | HardGrader(reply)", flush=True)
    print(f"[INFO] Model: {model} | Mode: {mode}", flush=True)

    results     = []
    total_score = 0.0

    for i, email in enumerate(emails, 1):

        # Reset env for this email
        obs = env.reset(email_id=email.id)

        # Triage: LLM or rule-based
        if use_llm:
            try:
                pred = llm_triage(obs.subject, obs.body, obs.sender)
            except Exception as e:
                print(f"[WARN] LLM failed on {email.id}: {e}. Using fallback.", flush=True)
                pred = rule_based_triage(obs.subject, obs.body)
        else:
            pred = rule_based_triage(obs.subject, obs.body)

        # Submit action to environment
        action    = Action(
            category=pred["category"],
            priority=pred["priority"],
            reply=pred["reply"],
        )
        step_resp = env.step(action)
        # reward is now a float (openenv-core compliant); detail is in reward_detail
        score     = step_resp.reward
        reward    = step_resp.reward_detail  # rich object with explanation/breakdown
        total_score += score

        # ── [STEP] ────────────────────────────────────────────────────────────
        # Build per-task scores from step response (required by Phase 2 validator)
        task_scores = [
            {
                "id":      t.id,
                "name":    t.name,
                "grader":  t.grader,
                "score":   round(t.score, 4),   # strictly between 0 and 1
                "weight":  t.weight,
            }
            for t in step_resp.tasks
        ]
        step_log = json.dumps({
            "event":    "step",
            "step":     i,
            "email_id": email.id,
            "subject":  email.subject,
            "action": {
                "category":  pred["category"],
                "priority":  pred["priority"],
                "reply_len": len(pred["reply"].split()),
            },
            "reward": {
                "score":       round(score, 4),
                "explanation": reward.explanation,
            },
            "expected": {
                "category": email.category.value,
                "priority": email.priority.value,
            },
            "tasks": task_scores,
        })
        print(f"[STEP] {step_log}", flush=True)

        # Store per-task scores for accurate [END] aggregation
        task_score_map = {t.id: t.score for t in step_resp.tasks}
        results.append({
            "email_id":           email.id,
            "subject":            email.subject,
            "predicted_category": pred["category"],
            "expected_category":  email.category.value,
            "predicted_priority": pred["priority"],
            "expected_priority":  email.priority.value,
            "score":              score,
            "task_1_score":       task_score_map.get("task_easy",   0.01),
            "task_2_score":       task_score_map.get("task_medium", 0.01),
            "task_3_score":       task_score_map.get("task_hard",   0.01),
        })

        if use_llm:
            time.sleep(0.5)   # respect HF rate limits

    # ── Aggregate metrics ─────────────────────────────────────────────────────
    n           = len(results)
    avg_score   = total_score / n if n else 0.01
    cat_correct = sum(1 for r in results if r["predicted_category"] == r["expected_category"])
    pri_correct = sum(1 for r in results if r["predicted_priority"] == r["expected_priority"])
    pass_count  = sum(1 for r in results if r["score"] >= 0.7)

    # ── [END] ─────────────────────────────────────────────────────────────────
    # Aggregate per-task scores — averaged directly from stored task scores
    def _clamp(v):
        return max(0.01, min(0.99, v))

    avg_cat_score = _clamp(round(sum(r["task_1_score"] for r in results) / n, 4)) if n else 0.01
    avg_pri_score = _clamp(round(sum(r["task_2_score"] for r in results) / n, 4)) if n else 0.01
    avg_rep_score = _clamp(round(sum(r["task_3_score"] for r in results) / n, 4)) if n else 0.01

    end_log = json.dumps({
        "event":             "end",
        "model":             model,
        "total_emails":      n,
        "total_score":       round(total_score, 4),
        "average_score":     round(avg_score,   4),
        "category_accuracy": round(cat_correct / n, 4) if n else 0.01,
        "priority_accuracy": round(pri_correct / n, 4) if n else 0.01,
        "pass_rate":         round(pass_count  / n, 4) if n else 0.01,
        "tasks": [
            {
                "id":      "task_easy",
                "name":    "Email Classification",
                "grader":  "server.graders:EasyGrader",
                "score":   avg_cat_score,
                "weight":  0.5,
            },
            {
                "id":      "task_medium",
                "name":    "Priority Detection",
                "grader":  "server.graders:MediumGrader",
                "score":   avg_pri_score,
                "weight":  0.3,
            },
            {
                "id":      "task_hard",
                "name":    "Reply Generation",
                "grader":  "server.graders:HardGrader",
                "score":   _clamp(avg_rep_score),
                "weight":  0.2,
            },
        ],
    })
    print(f"[END] {end_log}", flush=True)

    # Save results
    with open("baseline_results.json", "w") as f:
        json.dump({
            "model":            model,
            "mode":             mode,
            "total_emails":     n,
            "average_score":    round(avg_score, 4),
            "category_accuracy": round(cat_correct / n, 4) if n else 0.01,
            "priority_accuracy": round(pri_correct / n, 4) if n else 0.01,
            "pass_rate":         round(pass_count  / n, 4) if n else 0.01,
            "results":          results,
        }, f, indent=2)

    print("[INFO] Results saved -> baseline_results.json", flush=True)


if __name__ == "__main__":
    main()
