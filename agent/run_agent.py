import csv
import random
import sys
import json
from datetime import datetime
sys.path.append('agent')
from decision_engine import decide_action
from outcome_simulator import simulate_outcome

random.seed(42)

def load_transactions(filepath="data/transactions.csv"):
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        return list(reader)

def run():
    transactions = load_transactions()
    results = []

    for txn in transactions:
        decision = decide_action(txn)
        outcome = simulate_outcome(txn, decision)
        combined = {**txn, **decision, **outcome}
        results.append(combined)

    print(f"\nTotal transactions processed: {len(results)}\n")
    for r in results:
        print(f"{r['customer_id']} | ₹{int(r['amount']):>8} | {r['action']:<18} | {r['outcome']:<20} | {r['reason']}")

    # ---- SUMMARY ----
    total_at_risk = sum(int(r['amount']) for r in results)
    total_recovered = sum(int(r['recovered_amount']) for r in results if r['outcome'] == "RECOVERED")
    total_escalated = sum(int(r['amount']) for r in results if r['outcome'] == "PENDING_HUMAN_REVIEW")
    total_stopped = sum(int(r['amount']) for r in results if r['outcome'] == "STOPPED_BY_GUARDRAIL")
    total_not_recovered = sum(int(r['amount']) for r in results if r['outcome'] == "NOT_RECOVERED")

    attempted_amount = total_recovered + total_not_recovered
    recovery_rate = (total_recovered / total_at_risk * 100) if total_at_risk else 0
    attempt_success_rate = (total_recovered / attempted_amount * 100) if attempted_amount else 0

    print("\n" + "="*55)
    print("RECOVERX SUMMARY REPORT")
    print("="*55)
    print(f"Total revenue at risk:        ₹{total_at_risk:>12,}")
    print(f"Recovered:                    ₹{total_recovered:>12,}  ({recovery_rate:.1f}%)")
    print(f"Automated recovery attempted: ₹{attempted_amount:>12,}")
    print(f"Attempt success rate:         {attempt_success_rate:>13.1f}%")
    print(f"Escalated (human review):     ₹{total_escalated:>12,}")
    print(f"Stopped (guardrails):         ₹{total_stopped:>12,}")
    print(f"Attempted, not recovered:     ₹{total_not_recovered:>12,}")
    print("="*55)
    
        # ---- AUDIT TRAIL ----
    audit_log = []
    for r in results:
        audit_log.append({
            "transaction_id": r["customer_id"],
            "amount": int(r["amount"]),
            "failure_reason": r["failure_reason"],
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

    print(f"\nAudit log saved to data/audit_log.json ({len(audit_log)} entries)")

    return results

if __name__ == "__main__":
    run()