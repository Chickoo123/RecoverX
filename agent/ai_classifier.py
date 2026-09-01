import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

ALLOWED_INTENTS = {"DISPUTE", "FRAUD", "PROMISE_TO_PAY", "NONE"}
CACHE_VERSION = "safety-first-v3"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CACHE_PATH = PROJECT_ROOT / "data" / "ai_classification_cache.json"


def _cache_key(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _load_cache():
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not CACHE_PATH.exists():
        return {}
    try:
        with CACHE_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_cache(cache):
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temp = CACHE_PATH.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)
    temp.replace(CACHE_PATH)


def _normalize(text):
    return re.sub(r"\s+", " ", (text or "").strip().lower())


def _local_safety_intent(customer_reply):
    """Classify obvious high-risk language locally before any LLM call."""
    text = _normalize(customer_reply)

    fraud_terms = (
        "stolen card", "card stolen", "stolen", "fraud", "hacked", "scam",
        "someone else used my card", "someone used my card", "not me",
        "unauthorized use", "unauthorised use",
    )
    dispute_terms = (
        "already paid", "wrong charge", "charged twice", "duplicate charge",
        "chargeback", "dispute", "disputed", "please refund one",
        "never authorized this transaction", "never authorised this transaction",
    )
    promise_terms = (
        "pay next week", "pay tomorrow", "pay friday", "pay on friday",
        "pay next monday", "pay next month", "give me 2 days", "give me two days",
        "give me a few days", "pay in two days", "pay in a few days", "will pay",
        "i will pay", "i'll pay", "i can pay", "can pay", "let me pay", "clear this",
        "clear it", "settle this",
    )

    if any(term in text for term in fraud_terms):
        return "FRAUD", "Safety precheck detected a fraud-related phrase."
    if any(term in text for term in dispute_terms):
        return "DISPUTE", "Safety precheck detected a payment dispute."
    if any(term in text for term in promise_terms):
        return "PROMISE_TO_PAY", "Safety precheck detected a future-payment commitment."
    return None


def _fallback_intent(customer_reply):
    local = _local_safety_intent(customer_reply)
    if local:
        return local
    return "NONE", "AI classification was unavailable; deterministic policy continued safely."


def _extract_json(content):
    content = (content or "").strip()
    if not content:
        raise ValueError("empty model response")
    content = re.sub(r"^```(?:json)?\s*", "", content, flags=re.IGNORECASE)
    content = re.sub(r"\s*```$", "", content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start == -1 or end <= start:
            raise ValueError("model response did not contain a JSON object")
        return json.loads(content[start:end + 1])


def _groq_client():
    key = os.environ.get("GROQ_API_KEY")
    return Groq(api_key=key) if key else None


def classify_reply(customer_reply):
    """Classify customer context with safety-first routing and persistent caching."""
    if not customer_reply or not customer_reply.strip():
        return {"intent": "NONE", "ai_reasoning": "No customer reply available.", "classification_source": "none"}

    local = _local_safety_intent(customer_reply)
    if local:
        intent, reasoning = local
        return {"intent": intent, "ai_reasoning": reasoning, "classification_source": "safety_precheck"}

    key = _cache_key(customer_reply)
    cache = _load_cache()
    cached = cache.get(key)
    if isinstance(cached, dict) and cached.get("version") == CACHE_VERSION:
        intent = str(cached.get("intent", "NONE")).upper().strip()
        reasoning = str(cached.get("ai_reasoning", "")).strip()
        if intent in ALLOWED_INTENTS:
            return {"intent": intent, "ai_reasoning": reasoning or "Previously classified customer context.", "classification_source": "groq_cache"}

    client = _groq_client()
    if client is None:
        intent, reasoning = _fallback_intent(customer_reply)
        return {"intent": intent, "ai_reasoning": reasoning, "classification_source": "local_fallback"}

    prompt = f"""You are a financial recovery assistant.

Read this customer reply about a failed or pending payment:
"{customer_reply}"

Classify into exactly ONE intent:
DISPUTE
FRAUD
PROMISE_TO_PAY
NONE

Rules:
- DISPUTE = customer contests the charge/payment, says it was already paid,
  says billing is wrong/duplicated, or requests a billing review.
- FRAUD = customer reports theft, fraud, hacking, or another person using
  their card/account.
- PROMISE_TO_PAY = customer explicitly commits to paying later or asks for time.
- NONE = none of the above is clearly present.

Return ONLY a JSON object with these fields:
{{"intent":"NONE","reasoning":"short reason"}}"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=120,
        )
        parsed = _extract_json(response.choices[0].message.content or "")
        intent = str(parsed.get("intent", "NONE")).upper().strip()
        reasoning = str(parsed.get("reasoning", "")).strip()
        if intent not in ALLOWED_INTENTS:
            raise ValueError(f"unsupported intent: {intent}")
        reasoning = reasoning or "Model classified the customer context."
        cache[key] = {"version": CACHE_VERSION, "intent": intent, "ai_reasoning": reasoning}
        _save_cache(cache)
        return {"intent": intent, "ai_reasoning": reasoning, "classification_source": "groq"}
    except Exception:
        intent, reasoning = _fallback_intent(customer_reply)
        return {"intent": intent, "ai_reasoning": reasoning, "classification_source": "local_fallback"}
