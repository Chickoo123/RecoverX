import random

BASE_SUCCESS_PROBABILITY = {"RETRY": 0.65, "SEND_PAYMENT_LINK": 0.45, "SEND_REMINDER": 0.30}
FAILURE_REASON_ADJUSTMENT = {"network_error": 0.15, "card_expired": -0.05, "insufficient_funds": -0.20}


def simulate_outcome(transaction, decision):
    action = decision["action"]
    amount = int(transaction["amount"])

    if action == "ESCALATE":
        return {"outcome":"PENDING_HUMAN_REVIEW","recovered_amount":0,"follow_up_amount":0,"follow_up_channel":"","follow_up_status":"NOT_APPLICABLE","verification_status":"PENDING_HUMAN_REVIEW"}
    if action == "STOP":
        return {"outcome":"STOPPED_BY_GUARDRAIL","recovered_amount":0,"follow_up_amount":0,"follow_up_channel":"","follow_up_status":"NOT_APPLICABLE","verification_status":"BLOCKED_BY_GUARDRAIL"}
    if action == "SCHEDULE_FOLLOW_UP":
        channel = decision.get("follow_up_channel") or transaction.get("preferred_channel") or "email"
        return {"outcome":"FOLLOW_UP_SCHEDULED","recovered_amount":0,"follow_up_amount":amount,"follow_up_channel":channel,"follow_up_status":"SCHEDULED","verification_status":"PENDING"}

    probability = BASE_SUCCESS_PROBABILITY.get(action, 0.0) + FAILURE_REASON_ADJUSTMENT.get(transaction["failure_reason"], 0)
    probability = max(0.05, min(probability, 0.90))
    if random.random() < probability:
        return {"outcome":"RECOVERED","recovered_amount":amount,"follow_up_amount":0,"follow_up_channel":"","follow_up_status":"NOT_APPLICABLE","verification_status":"SIMULATED_SUCCESS"}
    return {"outcome":"NOT_RECOVERED","recovered_amount":0,"follow_up_amount":0,"follow_up_channel":"","follow_up_status":"NOT_APPLICABLE","verification_status":"SIMULATED_FAILURE"}
