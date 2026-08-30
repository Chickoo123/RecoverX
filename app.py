from flask import Flask, render_template, jsonify
import sys
sys.path.append('agent')
from decision_engine import decide_action
from outcome_simulator import simulate_outcome
from ai_classifier import classify_reply
import csv
import random
import json
from datetime import datetime

app = Flask(__name__)

def load_transactions(filepath="data/transactions.csv"):
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)

def run_simulation(transactions, use_ai=True):
    random.seed(42)
    results = []

    for original_txn in transactions:
        txn = dict(original_txn)  # copy so both runs start clean

        if use_ai:
            classification = classify_reply(txn.get("customer_reply", ""))
            txn["ai_intent"] = classification["intent"]
            txn["ai_reasoning"] = classification["ai_reasoning"]
        else:
            txn["ai_intent"] = "NONE"
            txn["ai_reasoning"] = ""

        decision = decide_action(txn)
        outcome = simulate_outcome(txn, decision)
        combined = {**txn, **decision, **outcome}
        results.append(combined)

    total_at_risk = sum(int(r['amount']) for r in results)
    total_recovered = sum(int(r['recovered_amount']) for r in results if r['outcome'] == "RECOVERED")
    total_escalated = sum(int(r['amount']) for r in results if r['outcome'] == "PENDING_HUMAN_REVIEW")
    total_stopped = sum(int(r['amount']) for r in results if r['outcome'] == "STOPPED_BY_GUARDRAIL")
    total_not_recovered = sum(int(r['amount']) for r in results if r['outcome'] == "NOT_RECOVERED")
    total_follow_up = sum(int(r['amount']) for r in results if r['outcome'] == "FOLLOW_UP_SCHEDULED")

    attempted_amount = total_recovered + total_not_recovered
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk else 0
    attempt_success_rate = (total_recovered / attempted_amount * 100) if attempted_amount else 0

    summary = {
        "total_at_risk": total_at_risk,
        "total_recovered": total_recovered,
        "recovery_rate": round(recovery_rate, 1),
        "attempted_amount": attempted_amount,
        "attempt_success_rate": round(attempt_success_rate, 1),
        "total_escalated": total_escalated,
        "total_stopped": total_stopped,
        "total_not_recovered": total_not_recovered,
        "total_follow_up": total_follow_up
    }

    return results, summary

def process_transactions():
    transactions = load_transactions()

    # Run WITH AI
    results_ai, summary_ai = run_simulation(transactions, use_ai=True)

    # Run WITHOUT AI (rules only, fallback)
    results_rules, summary_rules = run_simulation(transactions, use_ai=False)

    # Save audit log (AI version, since that's the "real" system)
    audit_log = []
    for r in results_ai:
        audit_log.append({
            "transaction_id": r["customer_id"],
            "amount": int(r["amount"]),
            "failure_reason": r["failure_reason"],
            "customer_reply": r.get("customer_reply", ""),
            "ai_intent": r.get("ai_intent", "NONE"),
            "ai_reasoning": r.get("ai_reasoning", ""),
            "decision": r["action"],
            "decision_reason": r["reason"],
            "guardrail_status": "PASSED" if not r["requires_human"] else "ESCALATED",
            "outcome": r["outcome"],
            "recovered_amount": int(r["recovered_amount"]),
            "verification_status": "SIMULATED_SUCCESS" if r["outcome"] == "RECOVERED" else "SIMULATED",
            "timestamp": datetime.now().isoformat()
        })
    with open("data/audit_log.json", "w") as f:
        json.dump(audit_log, f, indent=2)

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
        "summary_rules": summary_rules
    })

if __name__ == "__main__":
    app.run(debug=True, port=5000)