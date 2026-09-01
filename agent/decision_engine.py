HIGH_VALUE_THRESHOLD = 50000
MAX_RETRIES = 2
ESCALATE_OVERDUE_DAYS = 60
REMINDER_OVERDUE_DAYS = 30


def decide_action(transaction):
    """Apply hard financial guardrails first, then use AI context for routing."""
    amount = int(transaction["amount"])
    failure_reason = transaction["failure_reason"]
    attempt_count = int(transaction["attempt_count"])
    is_disputed = transaction["is_disputed"].strip().lower() == "true"
    days_overdue = int(transaction["days_overdue"])
    ai_intent = transaction.get("ai_intent", "NONE").upper().strip()
    ai_reasoning = transaction.get("ai_reasoning", "")

    if is_disputed:
        return {"action":"STOP","reason":"Payment is already marked disputed. Automated recovery is not allowed.","requires_human":True,"policy_rule":"DISPUTE_HARD_STOP"}
    if failure_reason == "fraud_suspected":
        return {"action":"ESCALATE","reason":"Fraud is suspected by the payment system. Human review is required.","requires_human":True,"policy_rule":"FRAUD_HUMAN_REVIEW"}
    if attempt_count >= MAX_RETRIES:
        return {"action":"STOP","reason":f"Already attempted {attempt_count} times. Stopping to avoid customer fatigue.","requires_human":False,"policy_rule":"RETRY_LIMIT_STOP"}
    if amount >= HIGH_VALUE_THRESHOLD:
        return {"action":"ESCALATE","reason":"High-value transaction requires human approval.","requires_human":True,"policy_rule":"HIGH_VALUE_APPROVAL"}
    if days_overdue >= ESCALATE_OVERDUE_DAYS:
        return {"action":"ESCALATE","reason":f"Overdue by {days_overdue} days. Too old for automated recovery.","requires_human":True,"policy_rule":"AGED_RECEIVABLE_REVIEW"}

    if ai_intent == "DISPUTE":
        return {"action":"STOP","reason":f'AI detected a dispute: "{ai_reasoning}"',"requires_human":True,"policy_rule":"AI_DISPUTE_STOP"}
    if ai_intent == "FRAUD":
        return {"action":"ESCALATE","reason":f'AI detected a fraud concern: "{ai_reasoning}"',"requires_human":True,"policy_rule":"AI_FRAUD_REVIEW"}
    if ai_intent == "PROMISE_TO_PAY":
        channel = transaction.get("preferred_channel", "email")
        return {"action":"SCHEDULE_FOLLOW_UP","reason":f'AI detected a promise to pay: "{ai_reasoning}"',"requires_human":False,"policy_rule":"PROMISE_TO_PAY_FOLLOW_UP","follow_up_channel":channel}

    if failure_reason == "network_error":
        return {"action":"RETRY","reason":"Temporary network error. Retrying payment.","requires_human":False,"policy_rule":"NETWORK_RETRY"}
    if failure_reason == "card_expired":
        return {"action":"SEND_PAYMENT_LINK","reason":"Card expired. Sending a payment link instead of retrying the old card.","requires_human":False,"policy_rule":"EXPIRED_CARD_PAYMENT_LINK"}
    if days_overdue >= REMINDER_OVERDUE_DAYS:
        return {"action":"SEND_REMINDER","reason":f"Overdue by {days_overdue} days. Sending a reminder.","requires_human":False,"policy_rule":"OVERDUE_REMINDER"}
    if failure_reason == "insufficient_funds":
        return {"action":"SEND_REMINDER","reason":"Insufficient funds. Sending a reminder instead of forcing a retry.","requires_human":False,"policy_rule":"INSUFFICIENT_FUNDS_REMINDER"}
    return {"action":"SEND_REMINDER","reason":f"Standard recovery case: {failure_reason}.","requires_human":False,"policy_rule":"DEFAULT_REMINDER"}
