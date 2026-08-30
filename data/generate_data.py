import csv
import random

random.seed(42)

def generate_amount(category):
    if category == "low":
        return random.randint(1000, 5000)
    elif category == "mid":
        return random.randint(5000, 25000)
    elif category == "high":
        return random.randint(50000, 90000)

# Sample customer replies per intent type
REPLIES = {
    "dispute": [
        "I already paid this last week, please check again.",
        "This charge is wrong, I never authorized this transaction.",
        "I was charged twice for the same order, please refund one.",
    ],
    "fraud": [
        "My card was stolen last month, this isn't me.",
        "I never made this purchase, someone else used my card.",
        "This looks like fraud, I don't recognize this transaction.",
    ],
    "promise_to_pay": [
        "Sorry, will pay tomorrow, just got my salary delayed.",
        "Give me 2 days, I'll clear this by Friday.",
        "Yes I'll pay, just need until next week.",
    ],
    "none": [
        "",
        "",
        "OK",
        "Sure",
        "",
    ]
}

def get_reply(scenario_name):
    if scenario_name == "disputed_case":
        return random.choice(REPLIES["dispute"])
    elif scenario_name == "fraud":
        return random.choice(REPLIES["fraud"])
    elif scenario_name in ("insufficient_funds", "max_retries"):
        # some of these are promise-to-pay, some are silent
        return random.choice(REPLIES["promise_to_pay"] + REPLIES["none"])
    else:
        return random.choice(REPLIES["none"])

SCENARIOS = [
    {"name": "retryable", "count": 10, "amount_category": "low",
     "failure_reason": "network_error", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 10)},

    {"name": "insufficient_funds", "count": 8, "amount_category": "mid",
     "failure_reason": "insufficient_funds", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 15)},

    {"name": "expired_card", "count": 8, "amount_category": "mid",
     "failure_reason": "card_expired", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 15)},

    {"name": "low_risk_mixed", "count": 6, "amount_category": "low",
     "failure_reason": "network_error", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 10)},

    {"name": "high_value", "count": 3, "amount_category": "high",
     "failure_reason": "bank_declined", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 20)},

    {"name": "fraud", "count": 4, "amount_category": "mid",
     "failure_reason": "fraud_suspected", "attempt_count_range": (0, 1),
     "disputed": False, "days_overdue_range": (0, 20)},

    {"name": "disputed_case", "count": 4, "amount_category": "mid",
     "failure_reason": "bank_declined", "attempt_count_range": (0, 1),
     "disputed": True, "days_overdue_range": (5, 20)},

    {"name": "max_retries", "count": 4, "amount_category": "mid",
     "failure_reason": "insufficient_funds", "attempt_count_range": (3, 4),
     "disputed": False, "days_overdue_range": (10, 30)},
]

CHANNELS = ["sms", "email", "whatsapp", "call"]

def generate_dataset():
    transactions = []
    customer_num = 1

    for scenario in SCENARIOS:
        for _ in range(scenario["count"]):
            attempt_count = random.randint(*scenario["attempt_count_range"])
            days_overdue = random.randint(*scenario["days_overdue_range"])

            txn = {
                "customer_id": f"CUST{customer_num:04d}",
                "amount": generate_amount(scenario["amount_category"]),
                "failure_reason": scenario["failure_reason"],
                "attempt_count": attempt_count,
                "previous_recovery_success": random.choice([True, False]),
                "days_overdue": days_overdue,
                "preferred_channel": random.choice(CHANNELS),
                "is_disputed": scenario["disputed"],
                "customer_reply": get_reply(scenario["name"]),
                "scenario": scenario["name"]
            }
            transactions.append(txn)
            customer_num += 1

    random.shuffle(transactions)
    return transactions

def save_to_csv(transactions, filepath="data/transactions.csv"):
    fieldnames = transactions[0].keys()
    with open(filepath, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(transactions)
    print(f"Saved {len(transactions)} transactions to {filepath}")

if __name__ == "__main__":
    data = generate_dataset()
    save_to_csv(data)