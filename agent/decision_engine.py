HIGH_VALUE_THRESHOLD = 50000
MAX_RETRIES = 2
ESCALATE_OVERDUE_DAYS = 60
REMINDER_OVERDUE_DAYS = 30

def decide_action(transaction):
    amount = int(transaction["amount"])
    failure_reason = transaction["failure_reason"]
    attempt_count = int(transaction["attempt_count"])
    is_disputed = transaction["is_disputed"] == "True"
    days_overdue = int(transaction["days_overdue"])
    previous_recovery_success = transaction["previous_recovery_success"] == "True"
    ai_intent = transaction.get("ai_intent", "NONE")
    ai_reasoning = transaction.get("ai_reasoning", "")

    if ai_intent == "DISPUTE":
        return {"action": "STOP", "reason": f'AI detected dispute: "{ai_reasoning}"', "requires_human": True}

    if ai_intent == "FRAUD":
        return {"action": "ESCALATE", "reason": f'AI detected fraud claim: "{ai_reasoning}"', "requires_human": True}

    if ai_intent == "PROMISE_TO_PAY":
        return {"action": "SCHEDULE_FOLLOW_UP", "reason": f'AI detected promise to pay: "{ai_reasoning}"', "requires_human": False}

    if is_disputed:
        return {"action": "STOP", "reason": "Payment is disputed. Automated recovery not allowed.", "requires_human": True}

    if failure_reason == "fraud_suspected":
        return {"action": "ESCALATE", "reason": "Fraud suspected. Requires manual review before any action.", "requires_human": True}

    if attempt_count >= MAX_RETRIES:
        return {"action": "STOP", "reason": f"Already attempted {attempt_count} times. Stopping to avoid customer fatigue.", "requires_human": False}

    if amount >= HIGH_VALUE_THRESHOLD:
        return {"action": "ESCALATE", "reason": f"High value transaction. Requires human approval.", "requires_human": True}

    if days_overdue >= ESCALATE_OVERDUE_DAYS:
        return {"action": "ESCALATE", "reason": f"Overdue by {days_overdue} days. Too old for automated retry.", "requires_human": True}

    if failure_reason == "network_error":
        return {"action": "RETRY", "reason": "Temporary network error. Retrying payment.", "requires_human": False}

    if failure_reason == "card_expired":
        return {"action": "SEND_PAYMENT_LINK", "reason": "Card expired. Sending payment link.", "requires_human": False}

    if days_overdue >= REMINDER_OVERDUE_DAYS:
        return {"action": "SEND_REMINDER", "reason": f"Overdue by {days_overdue} days. Sending reminder.", "requires_human": False}

    if failure_reason == "insufficient_funds":
        return {"action": "SEND_REMINDER", "reason": f"Insufficient funds. Sending reminder.", "requires_human": False}

    return {"action": "SEND_REMINDER", "reason": f"Standard case: {failure_reason}.", "requires_human": False}
