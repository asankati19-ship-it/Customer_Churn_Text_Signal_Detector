import unittest
import tempfile
from pathlib import Path

import pandas as pd

from churn_analyzer import analyze_dataframe, analyze_message, process_customer_dataset
from database import create_database, save_report_to_database, get_all_customers


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
        for value in ["", "  ", None, float("nan"), 123, "!!!", [], pd.NA]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                analyze_message(value)

    def test_context_regressions(self):
        examples = {
            "I do not want to cancel my subscription.": "Low",
            "I don’t want to cancel my subscription.": "Low",
            "I am not unhappy with the service.": "Low",
            "Please cancel my appointment.": "Low",
            "Please switch to dark mode.": "Low",
            "I want to switch to the annual plan.": "Low",
            "I use a switchboard.": "Low",
            "I contacted support and they solved my problem.": "Low",
            "My terrible connection was fixed.": "Low",
            "I will not renew my subscription.": "High",
            "I won't renew my subscription.": "High",
            "I am switching to another provider.": "High",
            "I may switch to another provider.": "Medium",
            "I do not want to cancel, but the service is too expensive.": "Medium",
            "Support was excellent, but please cancel my subscription.": "High",
            "I may cancel if this happens again.": "High",
            "I do not want to cancel. Now please cancel my account.": "High",
            "Please CANCEL   MY subscription.": "High",
            "The application does not work.": "Medium",
            "I have contacted support three times and nobody has fixed my problem.": "Medium",
        }
        for message, expected in examples.items():
            with self.subTest(message=message):
                result = analyze_message(message)
                self.assertEqual(result["risk_level"], expected)
                if expected == "Low":
                    self.assertEqual(result["matched_signals"], "None")

    def test_dataframe_validation(self):
        for frame in [pd.DataFrame(), pd.DataFrame({"recent_message": []}),
                      pd.DataFrame({"recent_message": ["hello", None]}),
                      pd.DataFrame([["hello", "hi"]], columns=["recent_message", " Recent_Message "])]:
            with self.subTest(frame=frame), self.assertRaises(ValueError):
                analyze_dataframe(frame)

    def test_batch_replaces_stale_predictions(self):
        frame = pd.DataFrame({" Recent_Message ": ["Cancel my subscription.", "Everything is fine."],
                              "risk_level": ["Low", "High"]})
        result = analyze_dataframe(frame)
        self.assertTrue(result.columns.is_unique)
        self.assertEqual(result.risk_level.tolist(), ["High", "Low"])

    def test_csv_database_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "input.csv"
            output = Path(directory) / "report.csv"
            db = Path(directory) / "test.db"
            pd.DataFrame({"customer_id": ["001"], "customer_name": ["Test"],
                          "recent_message": ["Please cancel my subscription."]}).to_csv(source, index=False)
            report = process_customer_dataset(source, output)
            self.assertEqual(report.iloc[0].customer_id, "001")
            create_database(db)
            save_report_to_database(report, db)
            self.assertEqual(get_all_customers(db).iloc[0].risk_level, "High")
            report.loc[0, "recent_message"] = "Everything is fine."
            save_report_to_database(analyze_dataframe(report), db)
            stored = get_all_customers(db)
            self.assertEqual(len(stored), 1)
            self.assertEqual(stored.iloc[0].risk_level, "Low")


if __name__ == "__main__":
    unittest.main()
