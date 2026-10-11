import unittest

from churn_analyzer import analyze_message


class TestChurnAnalyzer(unittest.TestCase):

    def test_cancellation_high_risk(self):
        result = analyze_message(
            "I am unhappy and want to cancel my subscription."
        )

        self.assertEqual(result["risk_level"], "High")
        self.assertIn(
            "cancel my subscription",
            result["matched_signals"],
        )

    def test_positive_customer_low_risk(self):
        result = analyze_message(
            "Everything is working well and I am very happy with the service."
        )

        self.assertEqual(result["risk_level"], "Low")

    def test_expensive_service_medium_risk(self):
        result = analyze_message(
            "The service is too expensive for me."
        )

        self.assertIn(
            result["risk_level"],
            ["Medium", "High"],
        )

        self.assertIn(
            "too expensive",
            result["matched_signals"],
        )

    def test_switching_signal(self):
        result = analyze_message(
            "I found a competitor and may switch next month."
        )

        self.assertIn(
            "competitor",
            result["matched_signals"],
        )

        self.assertIn(
            result["risk_level"],
            ["Medium", "High"],
        )

    def test_no_issues_positive_context(self):
        result = analyze_message(
            "Everything is fine. No issues so far."
        )

        self.assertEqual(result["risk_level"], "Low")

    def test_blank_message(self):
        result = analyze_message("")

        self.assertEqual(result["risk_level"], "Low")


if __name__ == "__main__":
    unittest.main()