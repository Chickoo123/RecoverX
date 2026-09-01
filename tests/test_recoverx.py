import unittest

from agent.decision_engine import decide_action
from agent.outcome_simulator import simulate_outcome


class RecoverXSafetyTests(unittest.TestCase):
    def base_txn(self, **overrides):
        txn = {"customer_id":"TEST001","amount":"12500","failure_reason":"network_error","attempt_count":"0","is_disputed":"False","days_overdue":"5","previous_recovery_success":"True","preferred_channel":"email","ai_intent":"NONE","ai_reasoning":""}
        txn.update(overrides)
        return txn

    def test_dispute_is_hard_stop(self):
        result = decide_action(self.base_txn(is_disputed="True"))
        self.assertEqual(result["action"], "STOP")
        self.assertEqual(result["policy_rule"], "DISPUTE_HARD_STOP")

    def test_retry_limit_is_hard_stop(self):
        result = decide_action(self.base_txn(attempt_count="3"))
        self.assertEqual(result["action"], "STOP")
        self.assertEqual(result["policy_rule"], "RETRY_LIMIT_STOP")

    def test_fraud_is_escalated(self):
        result = decide_action(self.base_txn(failure_reason="fraud_suspected"))
        self.assertEqual(result["action"], "ESCALATE")
        self.assertEqual(result["policy_rule"], "FRAUD_HUMAN_REVIEW")

    def test_promise_to_pay_is_follow_up(self):
        result = decide_action(self.base_txn(ai_intent="PROMISE_TO_PAY", ai_reasoning="Customer will pay next week."))
        self.assertEqual(result["action"], "SCHEDULE_FOLLOW_UP")

    def test_simulation_is_deterministic(self):
        txn = self.base_txn()
        decision = {"action":"RETRY"}
        random_state = __import__("random").getstate()
        try:
            first = simulate_outcome(txn, decision)
            __import__("random").setstate(random_state)
            second = simulate_outcome(txn, decision)
        finally:
            __import__("random").setstate(random_state)
        self.assertEqual(first, second)

    def test_follow_up_never_counts_as_recovered(self):
        result = simulate_outcome(self.base_txn(), {"action":"SCHEDULE_FOLLOW_UP"})
        self.assertEqual(result["outcome"], "FOLLOW_UP_SCHEDULED")
        self.assertEqual(result["recovered_amount"], 0)
        self.assertEqual(result["follow_up_amount"], 12500)


if __name__ == "__main__":
    unittest.main()
