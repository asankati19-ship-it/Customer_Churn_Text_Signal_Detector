import sqlite3
from datetime import datetime

import pandas as pd

from churn_analyzer import process_customer_dataset


DATABASE_FILE = "churn.db"


def create_database(db_path=DATABASE_FILE):
    """Create the SQLite churn database."""

    connection = sqlite3.connect(db_path)

    cursor = connection.cursor()

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS customer_churn (
            customer_id TEXT PRIMARY KEY,
            customer_name TEXT,
            recent_message TEXT,
            sentiment_score REAL,
            sentiment TEXT,
            matched_signals TEXT,
            positive_context TEXT,
            risk_score INTEGER,
            risk_level TEXT,
            retention_action TEXT,
            analyzed_at TEXT
        )
        """
    )

    connection.commit()
    connection.close()


def save_report_to_database(report, db_path=DATABASE_FILE):
    """Save or update churn analysis records."""

    connection = sqlite3.connect(db_path)

    cursor = connection.cursor()

    analyzed_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    for _, row in report.iterrows():

        cursor.execute(
            """
            INSERT INTO customer_churn (
                customer_id,
                customer_name,
                recent_message,
                sentiment_score,
                sentiment,
                matched_signals,
                positive_context,
                risk_score,
                risk_level,
                retention_action,
                analyzed_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(customer_id)
            DO UPDATE SET
                customer_name = excluded.customer_name,
                recent_message = excluded.recent_message,
                sentiment_score = excluded.sentiment_score,
                sentiment = excluded.sentiment,
                matched_signals = excluded.matched_signals,
                positive_context = excluded.positive_context,
                risk_score = excluded.risk_score,
                risk_level = excluded.risk_level,
                retention_action = excluded.retention_action,
                analyzed_at = excluded.analyzed_at
            """,
            (
                row["customer_id"],
                row["customer_name"],
                row["recent_message"],
                float(row["sentiment_score"]),
                row["sentiment"],
                row["matched_signals"],
                row["positive_context"],
                int(row["risk_score"]),
                row["risk_level"],
                row["retention_action"],
                analyzed_at,
            ),
        )

    connection.commit()
    connection.close()


def get_all_customers(db_path=DATABASE_FILE):
    """Return all CRM churn records."""

    connection = sqlite3.connect(db_path)

    query = """
        SELECT *
        FROM customer_churn
        ORDER BY
            CASE risk_level
                WHEN 'High' THEN 1
                WHEN 'Medium' THEN 2
                WHEN 'Low' THEN 3
                ELSE 4
            END,
            risk_score DESC,
            customer_id
    """

    df = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return df


def get_high_risk_customers(db_path=DATABASE_FILE):
    """Return only high-risk customers."""

    connection = sqlite3.connect(db_path)

    query = """
        SELECT
            customer_id,
            customer_name,
            recent_message,
            sentiment,
            matched_signals,
            risk_score,
            risk_level,
            retention_action
        FROM customer_churn
        WHERE risk_level = 'High'
        ORDER BY risk_score DESC, customer_id
    """

    df = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return df


def get_risk_summary(db_path=DATABASE_FILE):
    """Return High, Medium and Low customer counts."""

    connection = sqlite3.connect(db_path)

    query = """
        SELECT
            risk_level,
            COUNT(*) AS customer_count
        FROM customer_churn
        GROUP BY risk_level
    """

    summary = pd.read_sql_query(
        query,
        connection,
    )

    connection.close()

    return summary


def create_crm_report(
    output_file="crm_retention_report.csv",
):
    """Export SQLite data into CRM retention report."""

    report = get_all_customers()

    report.to_csv(
        output_file,
        index=False,
    )

    return report


if __name__ == "__main__":

    print(
        "Running Customer Churn CRM workflow..."
    )

    # Analyze customer messages
    analysis_report = process_customer_dataset()

    print(
        f"\nCustomers analyzed: {len(analysis_report)}"
    )

    # Create database
    create_database()

    print(
        "SQLite database created successfully."
    )

    # Save results
    save_report_to_database(
        analysis_report
    )

    print(
        "Customer churn records saved to database."
    )

    # Create CRM report
    create_crm_report()

    print(
        "CRM retention report created successfully."
    )

    # Show risk summary
    risk_summary = get_risk_summary()

    print(
        "\n=============================="
    )

    print(
        "CRM CHURN RISK SUMMARY"
    )

    print(
        "=============================="
    )

    print(
        risk_summary.to_string(
            index=False
        )
    )

    # Show high-risk customers
    high_risk = get_high_risk_customers()

    print(
        "\n=============================="
    )

    print(
        "HIGH-RISK CUSTOMERS"
    )

    print(
        "=============================="
    )

    if high_risk.empty:

        print(
            "No high-risk customers found."
        )

    else:

        print(
            high_risk[
                [
                    "customer_id",
                    "customer_name",
                    "risk_score",
                    "matched_signals",
                    "retention_action",
                ]
            ].to_string(
                index=False
            )
        )

    print(
        "\nCRM workflow completed successfully."
    )

    print(
        "Database file: churn.db"
    )

    print(
        "CRM report: crm_retention_report.csv"
    )