import unittest

from churn_analyzer import analyze_message, find_keywords, CANCELLATION_KEYWORDS


class TestChurnAnalyzer(unittest.TestCase):

    def test_negated_cancellation_and_switching(self):
        result = analyze_message(
            "I do not want to cancel my subscription. "
            "I am not switching to a competitor."
        )
        self.assertEqual(result["risk_level"], "Low")
        self.assertEqual(result["matched_signals"], "None")

    def test_contracted_negation(self):
        for message in ["I don't want to cancel my subscription.",
                        "I don’t want to cancel my subscription.",
                        "I won't switch to a competitor."]:
            with self.subTest(message=message):
                self.assertEqual(analyze_message(message)["matched_signals"], "None")

    def test_other_complaint_survives_negation(self):
        result = analyze_message(
            "I do not want to cancel, but your service is terrible."
        )
        self.assertIn("terrible", result["matched_signals"])
        self.assertNotIn("cancel", result["matched_signals"])

    def test_unrelated_negation_does_not_hide_cancellation(self):
        for message in ["I am not happy and want to cancel my subscription.",
                        "I do not want to cancel. Actually, cancel my subscription.",
                        "I do not want to continue."]:
            with self.subTest(message=message):
                self.assertEqual(analyze_message(message)["risk_level"], "High")

    def test_negated_positive_phrase_does_not_override_complaint(self):
        result = analyze_message("The service is not excellent. I am miserable.")
        self.assertEqual(result["positive_context"], "None")
        self.assertNotEqual(result["risk_level"], "Low")

    def test_keyword_word_boundaries(self):
        self.assertEqual(find_keywords("An uncancelled appointment", CANCELLATION_KEYWORDS), [])

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
