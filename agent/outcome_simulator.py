import random

BASE_SUCCESS_PROBABILITY = {
    "RETRY": 0.65,
    "SEND_PAYMENT_LINK": 0.45,
    "SEND_REMINDER": 0.30,
}

FAILURE_REASON_ADJUSTMENT = {
    "network_error": 0.15,
    "card_expired": -0.05,
    "insufficient_funds": -0.20,
}

def simulate_outcome(transaction, decision):
    action = decision["action"]
    amount = int(transaction["amount"])

    if action in ("ESCALATE",):
        return {
            "outcome": "PENDING_HUMAN_REVIEW",
            "recovered_amount": 0
        }

    if action == "STOP":
        return {
            "outcome": "STOPPED_BY_GUARDRAIL",
            "recovered_amount": 0
        }

    probability = BASE_SUCCESS_PROBABILITY.get(action, 0.0)
    probability += FAILURE_REASON_ADJUSTMENT.get(transaction["failure_reason"], 0)
    probability = max(0.05, min(probability, 0.90))

    recovered = random.random() < probability

    if recovered:
        return {
            "outcome": "RECOVERED",
            "recovered_amount": amount
        }

    return {
        "outcome": "NOT_RECOVERED",
        "recovered_amount": 0
    }