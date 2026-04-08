"""
hf_agent.py — OpenAI-compatible HuggingFace Inference Agent

Uses OpenAI client pointed at HuggingFace's router endpoint.
Primary model : meta-llama/Llama-3.1-8B-Instruct  (Meta · PyTorch hackathon)
Fallback model: Qwen/Qwen2.5-7B-Instruct           (fully open)

Required env vars:
  HF_TOKEN    — HuggingFace token (required for LLM inference)
  MODEL_NAME  — override default model (optional)
"""

import os
import json
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# ── Model config ──────────────────────────────────────────────────────────────

PRIMARY_MODEL  = os.getenv("MODEL_NAME", "gpt-4o-mini")
FALLBACK_MODEL = "gpt-3.5-turbo"
HF_TOKEN       = os.getenv("HF_TOKEN", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Use OpenAI if OPENAI_API_KEY is set, else HuggingFace router
API_KEY        = OPENAI_API_KEY or HF_TOKEN
HF_BASE_URL    = None if OPENAI_API_KEY else "https://router.huggingface.co/v1"

VALID_CATEGORIES = ["Billing Refund", "Account", "Feature Request", "Technical Support"]
VALID_PRIORITIES = ["Low", "Medium", "High"]

# ── System prompt ─────────────────────────────────────────────────────────────

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


# ── HuggingFace agent (OpenAI-compatible client) ──────────────────────────────

class HuggingFaceAgent:
    """Calls HuggingFace router via OpenAI client for email triage predictions."""

    def __init__(self):
        self._client = None
        self._model  = PRIMARY_MODEL
        self._ready  = False
        self._init()

    def _init(self):
        if not API_KEY:
            logger.warning("No API key set — using rule-based fallback.")
            return
        try:
            from openai import OpenAI
            kwargs = {"api_key": API_KEY}
            if HF_BASE_URL:
                kwargs["base_url"] = HF_BASE_URL
            self._client = OpenAI(**kwargs)
            self._ready  = True
            provider = "OpenAI" if OPENAI_API_KEY else "HuggingFace"
            logger.info(f"{provider} agent ready — model: {self._model}")
        except Exception as e:
            logger.error(f"Failed to initialize client: {e}")

    @property
    def is_ready(self) -> bool:
        return self._ready

    @property
    def model_name(self) -> str:
        return self._model if self._ready else "rule-based"

    @property
    def provider(self) -> str:
        if not self._ready:
            return "rule-based"
        return "openai" if OPENAI_API_KEY else "huggingface"

    def predict(self, subject: str, body: str, sender: str = "") -> dict:
        """
        Run triage prediction on an email.
        Returns dict with: category, priority, reply, model
        Falls back to rule-based if HF is unavailable.
        """
        if not self._ready:
            return {**_rule_based(subject, body), "model": "rule-based"}

        user_message = (
            f"Subject: {subject}\n"
            f"From: {sender}\n\n"
            f"{body[:2000]}"
        )

        # Try primary model, then fallback
        for model in [self._model, FALLBACK_MODEL]:
            try:
                result = self._call_llm(model, user_message)
                result["model"] = model
                return result
            except Exception as e:
                logger.warning(f"Model {model} failed: {e}. Trying next...")

        logger.warning("All LLM models failed — using rule-based fallback.")
        return {**_rule_based(subject, body), "model": "rule-based (fallback)"}

    def _call_llm(self, model: str, user_message: str) -> dict:
        kwargs = {
            "model": model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_message},
            ],
            "max_tokens": 600,
            "temperature": 0.1,
        }
        # JSON mode only supported by OpenAI (not all HF models)
        if OPENAI_API_KEY:
            kwargs["response_format"] = {"type": "json_object"}
        response = self._client.chat.completions.create(**kwargs)
        content = response.choices[0].message.content.strip()
        return _parse_response(content)


# ── Response parser ───────────────────────────────────────────────────────────

def _parse_response(content: str) -> dict:
    """Extract JSON from LLM response, with cleanup for common issues."""
    content = re.sub(r"```(?:json)?\s*", "", content).strip("` \n")
    match = re.search(r"\{.*\}", content, re.DOTALL)
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

    reply = data.get("reply", "").strip()
    if not reply:
        raise ValueError("Empty reply in LLM response")

    return {"category": category, "priority": priority, "reply": reply}


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_based(subject: str, body: str) -> dict:
    """Pure keyword matching — used when HF_TOKEN is not set."""
    text = f"{subject} {body}".lower()

    category = "Technical Support"
    if any(w in text for w in ["refund", "charge", "billing", "invoice", "payment",
                                "price", "cost", "discount", "subscription fee"]):
        category = "Billing Refund"
    elif any(w in text for w in ["account", "login", "password", "reset", "2fa",
                                  "two-factor", "access", "profile", "locked out"]):
        category = "Account"
    elif any(w in text for w in ["feature", "suggest", "request", "idea",
                                  "integration", "export", "dark mode", "slack"]):
        category = "Feature Request"

    priority = "Medium"
    if any(w in text for w in ["urgent", "asap", "immediately", "critical", "crash",
                                "locked out", "charged twice", "duplicate", "deadline"]):
        priority = "High"
    elif any(w in text for w in ["suggestion", "idea", "would be nice",
                                  "consider", "could you", "minor"]):
        priority = "Low"

    reply = (
        f"Dear Customer,\n\n"
        f"Thank you for reaching out to us. We sincerely apologize for the inconvenience "
        f"regarding \"{subject}\". Our support team will investigate this matter "
        f"immediately and provide a resolution within 24 hours.\n\n"
        f"Please don't hesitate to reply if you need further assistance.\n\n"
        f"Best regards,\nSupport Team"
    )

    return {"category": category, "priority": priority, "reply": reply}


# ── Singleton instance (shared across requests) ───────────────────────────────

_agent: Optional[HuggingFaceAgent] = None


def get_agent() -> HuggingFaceAgent:
    global _agent
    if _agent is None:
        _agent = HuggingFaceAgent()
    return _agent
