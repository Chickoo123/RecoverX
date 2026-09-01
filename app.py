import csv
import json
import random
import sys
from datetime import datetime
from pathlib import Path

from flask import Flask, jsonify, render_template

sys.path.insert(0, "agent")
from ai_classifier import classify_reply
from decision_engine import decide_action
from outcome_simulator import simulate_outcome

app = Flask(__name__)
PROJECT_ROOT = Path(__file__).resolve().parent
AUDIT_PATH = PROJECT_ROOT / "data" / "audit_log.json"


def load_transactions(filepath="data/transactions.csv"):
    with open(filepath, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def run_simulation(transactions, use_ai=True):
    random.seed(42)
    results = []
    for original_txn in transactions:
        txn = dict(original_txn)
        if use_ai:
            classification = classify_reply(txn.get("customer_reply", ""))
            txn["ai_intent"] = classification["intent"]
            txn["ai_reasoning"] = classification["ai_reasoning"]
            txn["classification_source"] = classification.get("classification_source", "unknown")
        else:
            txn["ai_intent"] = "NONE"
            txn["ai_reasoning"] = ""
            txn["classification_source"] = "rules_only"

        decision = decide_action(txn)
        outcome = simulate_outcome(txn, decision)
        results.append({**txn, **decision, **outcome})

    total_at_risk = sum(int(r["amount"]) for r in results)
    total_recovered = sum(int(r["recovered_amount"]) for r in results if r["outcome"] == "RECOVERED")
    total_escalated = sum(int(r["amount"]) for r in results if r["outcome"] == "PENDING_HUMAN_REVIEW")
    total_stopped = sum(int(r["amount"]) for r in results if r["outcome"] == "STOPPED_BY_GUARDRAIL")
    total_not_recovered = sum(int(r["amount"]) for r in results if r["outcome"] == "NOT_RECOVERED")
    total_follow_up = sum(int(r["follow_up_amount"]) for r in results if r["outcome"] == "FOLLOW_UP_SCHEDULED")
    attempted_amount = total_recovered + total_not_recovered
    return results, {
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "recovery_rate": round(total_recovered / total_at_risk * 100, 1) if total_at_risk else 0,
        "attempted_amount": attempted_amount,
        "attempt_success_rate": round(total_recovered / attempted_amount * 100, 1) if attempted_amount else 0,
        "total_escalated": total_escalated,
        "total_stopped": total_stopped,
        "total_not_recovered": total_not_recovered,
        "total_follow_up": total_follow_up,
    }


def process_transactions():
    transactions = load_transactions()
    results_ai, summary_ai = run_simulation(transactions, True)
    results_rules, summary_rules = run_simulation(transactions, False)

    audit_log = []
    for r in results_ai:
        guardrail_status = "BLOCKED" if r["action"] == "STOP" else ("REVIEW_REQUIRED" if r["action"] == "ESCALATE" else "PASSED")
        audit_log.append({
            "transaction_id": r["customer_id"],
            "amount": int(r["amount"]),
            "failure_reason": r["failure_reason"],
            "customer_reply": r.get("customer_reply", ""),
            "ai_intent": r.get("ai_intent", "NONE"),
            "ai_reasoning": r.get("ai_reasoning", ""),
            "classification_source": r.get("classification_source", "unknown"),
            "decision": r["action"],
            "decision_reason": r["reason"],
            "policy_rule": r.get("policy_rule", ""),
            "guardrail_status": guardrail_status,
            "outcome": r["outcome"],
            "recovered_amount": int(r["recovered_amount"]),
            "follow_up_amount": int(r.get("follow_up_amount", 0)),
            "follow_up_channel": r.get("follow_up_channel", ""),
            "verification_status": r.get("verification_status", "SIMULATED"),
            "timestamp": datetime.now().isoformat(),
        })
    AUDIT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_PATH.open("w", encoding="utf-8") as f:
        json.dump(audit_log, f, indent=2, ensure_ascii=False)
    return results_ai, summary_ai, results_rules, summary_rules


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/run")
def run_agent():
    results_ai, summary_ai, results_rules, summary_rules = process_transactions()
    return jsonify({
        "results_ai": results_ai,
        "summary_ai": summary_ai,
        "results_rules": results_rules,
        "summary_rules": summary_rules,
    })


if __name__ == "__main__":
    app.run(debug=True, port=5000)
