import os
from dotenv import load_dotenv
from groq import Groq
import json
import re

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def classify_reply(customer_reply):
    """
    Reads a customer's unstructured reply and classifies intent.
    Returns: dict with intent, ai_reasoning
    """
    if not customer_reply or customer_reply.strip() == "":
        return {
            "intent": "NONE",
            "ai_reasoning": "No customer reply available."
        }

    prompt = f"""You are a financial recovery assistant. Read this customer reply about a failed/pending payment and classify their intent.

Customer reply: "{customer_reply}"

Classify into exactly one of: DISPUTE, FRAUD, PROMISE_TO_PAY, NONE

Respond with ONLY a single line of valid JSON, nothing else, no explanation, no markdown:
{{"intent": "DISPUTE", "reasoning": "short reason here"}}
"""

    try:
        response = client.chat.completions.create(
            model="openai/gpt-oss-20b",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=200
        )
        content = response.choices[0].message.content.strip()

        # Extract JSON object using regex (handles extra text around it)
        match = re.search(r'\{.*\}', content, re.DOTALL)
        if match:
            content = match.group(0)

        parsed = json.loads(content)
        return {
            "intent": parsed.get("intent", "NONE"),
            "ai_reasoning": parsed.get("reasoning", "")
        }
    except Exception as e:
        return {
            "intent": "NONE",
            "ai_reasoning": f"Classification unavailable: {str(e)}",
            "raw_debug": content if 'content' in dir() else "no response"
        }