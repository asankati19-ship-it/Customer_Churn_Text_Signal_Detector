"""Exercise Streamlit reruns without touching the user's CRM database."""
import tempfile
import unittest
from contextlib import ExitStack
from functools import partial
from pathlib import Path
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
import database


class TestApp(unittest.TestCase):
    def test_generated_id_and_dashboard_filters(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            db = Path(directory) / "app.db"
            for name in ["create_database", "save_report_to_database", "get_all_customers",
                         "get_high_risk_customers", "get_risk_summary"]:
                stack.enter_context(patch.object(database, name, partial(getattr(database, name), db_path=db)))
            app = AppTest.from_file("app.py", default_timeout=20).run()
            app.text_area[0].set_value("Please cancel my subscription.")
            app.button(key="analyze_single").click().run()
            app.button(key="save_single_customer").click().run()
            saved = database.get_all_customers()
            self.assertTrue(saved.iloc[0].customer_id.startswith("CUST-"))
            app.button(key="save_single_customer").click().run()
            self.assertEqual(len(database.get_all_customers()), 1)
            app.text_input(key="crm_search").set_value("no-match").run()
            self.assertTrue(any("Showing 0 of 1" in c.value for c in app.caption))
            app.text_input(key="crm_search").set_value("").run()
            app.multiselect(key="crm_risk").set_value([]).run()
            self.assertTrue(any("Showing 0 of 1" in c.value for c in app.caption))
            app.multiselect(key="crm_risk").set_value(["High"]).run()
            self.assertTrue(any("Showing 1 of 1" in c.value for c in app.caption))
            self.assertEqual(len(app.exception), 0)
            self.assertFalse(any("Unable to" in e.value for e in app.error))

    def test_analyze_edit_and_save(self):
        with tempfile.TemporaryDirectory() as directory, ExitStack() as stack:
            db = Path(directory) / "app.db"
            for name in ["create_database", "save_report_to_database", "get_all_customers",
                         "get_high_risk_customers", "get_risk_summary"]:
                stack.enter_context(patch.object(database, name, partial(getattr(database, name), db_path=db)))
            app = AppTest.from_file("app.py", default_timeout=20).run()
            self.assertEqual(len(app.exception), 0)
            app.text_input[0].set_value("001")
            app.text_area[0].set_value("Please cancel my subscription.")
            app.button(key="analyze_single").click().run()
            self.assertEqual(app.session_state["single_result"]["risk_level"], "High")
            app.button(key="save_single_customer").click().run()
            self.assertEqual(database.get_all_customers().iloc[0].risk_level, "High")
            app.text_area[0].set_value("I do not want to cancel my subscription.").run()
            self.assertNotIn("single_result", app.session_state)
            self.assertFalse(any(button.key == "save_single_customer" for button in app.button))
            app.button(key="analyze_single").click().run()
            self.assertEqual(app.session_state["single_result"]["risk_level"], "Low")
            app.button(key="save_single_customer").click().run()
            self.assertEqual(database.get_all_customers().iloc[0].risk_level, "Low")
            app.text_area[0].set_value("!!!").run()
            app.button(key="analyze_single").click().run()
            self.assertNotIn("single_result", app.session_state)
            self.assertEqual(len(app.exception), 0)


