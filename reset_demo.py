"""Build a fresh, separate demo database; never overwrite an existing database."""
import argparse
import os
from pathlib import Path
from churn_analyzer import analyze_dataframe
from database import create_database, save_report_to_database
import pandas as pd


def build_demo(destination):
    destination = Path(destination)
    rows = pd.read_csv(Path(__file__).with_name("test_customers_40.csv"), dtype=str)
    if len(rows) != 40 or not rows.customer_id.is_unique:
        raise ValueError("Demo fixture must contain exactly 40 unique customers.")
    report = analyze_dataframe(rows)
    descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    os.close(descriptor)
    try:
        create_database(destination)
        save_report_to_database(report, destination)
    except Exception:
        destination.unlink(missing_ok=True)
        raise
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", help="A new database path that does not already exist")
    report = build_demo(parser.parse_args().destination)
    print(f"Created {len(report)} demo records. Existing CRM data was not changed.")

