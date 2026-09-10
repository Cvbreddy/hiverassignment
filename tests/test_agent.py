import unittest

from hiver_agent.agent import Example, SupportAgent, classify


class AgentTests(unittest.TestCase):
    def setUp(self):
        self.agent = SupportAgent([
            Example("where is my package", "delivery_tracking", "check tracking", "Please DM your order number so we can check tracking."),
            Example("I was charged twice", "billing_refund", "refund duplicate", "Please DM your order details so we can investigate."),
        ])

    def test_classifies_clear_delivery_request(self):
        self.assertEqual(classify("Can I get tracking for my order?")[0], "delivery_tracking")

    def test_sensitive_request_escalates(self):
        prediction = self.agent.predict("I need to send my credit card number")
        self.assertEqual(prediction.action, "escalate")
        self.assertIn("sensitive", prediction.escalation_reason)

    def test_reply_has_historical_evidence(self):
        prediction = self.agent.predict("I was charged twice")
        self.assertEqual(prediction.intent, "billing_refund")
        self.assertTrue(prediction.evidence)


if __name__ == "__main__":
    unittest.main()
