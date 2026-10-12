import pandas as pd
import streamlit as st

from churn_analyzer import analyze_message
from database import (
    create_database,
    get_all_customers,
    get_high_risk_customers,
    get_risk_summary,
    save_report_to_database,
)


# =================================================
# PAGE CONFIGURATION
# =================================================

st.set_page_config(
    page_title="Customer Churn Text Signal Detector",
    page_icon="📉",
    layout="wide",
)


# =================================================
# INITIALIZE SQLITE DATABASE
# =================================================

create_database()


# =================================================
# SIDEBAR
# =================================================

st.sidebar.title("📉 Churn Detector")

st.sidebar.write(
    """
    This CRM tool analyzes recent customer messages using:

    • VADER sentiment analysis  
    • Churn keyword rules  
    • Risk scoring  
    • Retention recommendations
    """
)

st.sidebar.info(
    "Risk levels: 🔴 High | 🟠 Medium | 🟢 Low"
)


# =================================================
# MAIN HEADER
# =================================================

st.title("📉 Customer Churn Text Signal Detector")

st.write(
    "Identify dissatisfaction, cancellation, and switching "
    "signals from customer messages and generate CRM "
    "retention follow-up recommendations."
)

st.divider()


# =================================================
# TABS
# =================================================

single_tab, bulk_tab, dashboard_tab = st.tabs(
    [
        "👤 Single Customer Analysis",
        "📁 Bulk CRM Analysis",
        "📊 Retention Dashboard",
    ]
)


# =================================================
# TAB 1 - SINGLE CUSTOMER ANALYSIS
# =================================================

with single_tab:

    st.subheader("Analyze a Customer Message")

    col1, col2 = st.columns(2)

    with col1:
        customer_id = st.text_input(
            "Customer ID",
            placeholder="Example: C101",
        )

    with col2:
        customer_name = st.text_input(
            "Customer Name",
            placeholder="Example: Customer 101",
        )

    message = st.text_area(
        "Recent Customer Message",
        placeholder=(
            "Example: I am very unhappy with the service "
            "and I want to cancel my subscription."
        ),
        height=150,
    )

    if st.button(
        "🔍 Analyze Message",
        type="primary",
        key="analyze_single",
    ):

        if not message.strip():

            st.warning(
                "Please enter a customer message."
            )

        else:

            result = analyze_message(message)

            st.session_state["single_result"] = result
            st.session_state["single_message"] = message
            st.session_state["single_customer_id"] = customer_id
            st.session_state["single_customer_name"] = customer_name


    # -------------------------------------------------
    # DISPLAY SINGLE CUSTOMER RESULT
    # -------------------------------------------------

    if "single_result" in st.session_state:

        result = st.session_state["single_result"]

        st.divider()

        risk_level = result["risk_level"]


        # ---------------------------------------------
        # RISK FLAG
        # ---------------------------------------------

        if risk_level == "High":

            st.error(
                "🔴 HIGH CHURN RISK"
            )

        elif risk_level == "Medium":

            st.warning(
                "🟠 MEDIUM CHURN RISK"
            )

        else:

            st.success(
                "🟢 LOW CHURN RISK"
            )


        # ---------------------------------------------
        # METRICS
        # ---------------------------------------------

        col1, col2, col3 = st.columns(3)

        with col1:

            st.metric(
                "Sentiment",
                result["sentiment"],
            )

        with col2:

            st.metric(
                "Sentiment Score",
                result["sentiment_score"],
            )

        with col3:

            st.metric(
                "Risk Score",
                result["risk_score"],
            )


        # ---------------------------------------------
        # DETECTED SIGNALS
        # ---------------------------------------------

        st.subheader(
            "Detected Churn Signals"
        )

        st.write(
            result["matched_signals"]
        )


        # ---------------------------------------------
        # POSITIVE CONTEXT
        # ---------------------------------------------

        st.subheader(
            "Positive Context"
        )

        st.write(
            result["positive_context"]
        )


        # ---------------------------------------------
        # RETENTION ACTION
        # ---------------------------------------------

        st.subheader(
            "Recommended Retention Action"
        )

        st.info(
            result["retention_action"]
        )


        # ---------------------------------------------
        # SAVE CUSTOMER TO CRM
        # ---------------------------------------------

        if st.button(
            "💾 Save Customer to CRM",
            key="save_single_customer",
        ):

            saved_customer_id = (
                st.session_state[
                    "single_customer_id"
                ].strip()
            )

            saved_customer_name = (
                st.session_state[
                    "single_customer_name"
                ].strip()
            )

            if not saved_customer_id:

                st.warning(
                    "Please enter a Customer ID "
                    "before saving to CRM."
                )

            else:

                if not saved_customer_name:

                    saved_customer_name = (
                        saved_customer_id
                    )

                row = {
                    "customer_id": (
                        saved_customer_id
                    ),
                    "customer_name": (
                        saved_customer_name
                    ),
                    "recent_message": (
                        st.session_state[
                            "single_message"
                        ]
                    ),
                    "sentiment_score": (
                        result[
                            "sentiment_score"
                        ]
                    ),
                    "sentiment": (
                        result["sentiment"]
                    ),
                    "matched_signals": (
                        result[
                            "matched_signals"
                        ]
                    ),
                    "positive_context": (
                        result[
                            "positive_context"
                        ]
                    ),
                    "risk_score": (
                        result["risk_score"]
                    ),
                    "risk_level": (
                        result["risk_level"]
                    ),
                    "retention_action": (
                        result[
                            "retention_action"
                        ]
                    ),
                }

                single_df = pd.DataFrame(
                    [row]
                )

                try:

                    save_report_to_database(
                        single_df
                    )

                    st.success(
                        "Customer saved to CRM successfully."
                    )

                except Exception as error:

                    st.error(
                        f"Unable to save customer: {error}"
                    )


# =================================================
# TAB 2 - BULK CRM ANALYSIS
# =================================================

with bulk_tab:

    st.subheader(
        "Bulk Customer Message Analysis"
    )

    st.write(
        "Upload a CSV containing customer messages."
    )

    st.write(
        "Recommended columns: "
        "`customer_id`, `customer_name`, "
        "`recent_message`"
    )


    # -------------------------------------------------
    # SAMPLE DATA
    # -------------------------------------------------

    sample_data = pd.DataFrame(
        {
            "customer_id": [
                "C001",
                "C002",
                "C003",
            ],
            "customer_name": [
                "Customer 01",
                "Customer 02",
                "Customer 03",
            ],
            "recent_message": [
                (
                    "I want to cancel my "
                    "subscription immediately."
                ),
                (
                    "The service is too expensive "
                    "and I may switch providers."
                ),
                (
                    "Everything is working well "
                    "and I am happy."
                ),
            ],
        }
    )

    sample_csv = (
        sample_data
        .to_csv(index=False)
        .encode("utf-8")
    )

    st.download_button(
        label="⬇️ Download Sample CSV",
        data=sample_csv,
        file_name="sample_customer_messages.csv",
        mime="text/csv",
    )


    # -------------------------------------------------
    # FILE UPLOAD
    # -------------------------------------------------

    uploaded_file = st.file_uploader(
        "Choose customer CSV file",
        type=["csv"],
        key="bulk_upload",
    )


    if uploaded_file is not None:

        try:

            df = pd.read_csv(
                uploaded_file
            )


            # -----------------------------------------
            # CLEAN COLUMN NAMES
            # -----------------------------------------

            df.columns = [
                str(column)
                .strip()
                .lower()
                for column in df.columns
            ]


            # -----------------------------------------
            # VALIDATE REQUIRED COLUMN
            # -----------------------------------------

            if "recent_message" not in df.columns:

                st.error(
                    "CSV must contain a "
                    "'recent_message' column."
                )

            else:

                # -------------------------------------
                # GENERATE CUSTOMER IDs IF MISSING
                # -------------------------------------

                if "customer_id" not in df.columns:

                    df["customer_id"] = [
                        f"C{i:03d}"
                        for i in range(
                            1,
                            len(df) + 1,
                        )
                    ]


                # -------------------------------------
                # GENERATE CUSTOMER NAMES IF MISSING
                # -------------------------------------

                if (
                    "customer_name"
                    not in df.columns
                ):

                    df["customer_name"] = [
                        f"Customer {i:02d}"
                        for i in range(
                            1,
                            len(df) + 1,
                        )
                    ]


                st.success(
                    "CSV uploaded successfully."
                )


                # -------------------------------------
                # DATA PREVIEW
                # -------------------------------------

                st.subheader(
                    "Uploaded Data Preview"
                )

                st.dataframe(
                    df.head(10),
                    width="stretch",
                )


                # -------------------------------------
                # ANALYZE CUSTOMERS
                # -------------------------------------

                st.caption(
                    "Analyzing this file also saves the results to CRM."
                )

                if st.button(
                    "🚀 Analyze and Save to CRM",
                    type="primary",
                    key="analyze_bulk",
                ):

                    with st.spinner(
                        "Analyzing customer messages..."
                    ):

                        analysis_results = (
                            df[
                                "recent_message"
                            ]
                            .apply(
                                analyze_message
                            )
                            .apply(
                                pd.Series
                            )
                        )


                        report = pd.concat(
                            [
                                df.reset_index(
                                    drop=True
                                ),
                                analysis_results
                                .reset_index(
                                    drop=True
                                ),
                            ],
                            axis=1,
                        )


                        # ---------------------------------
                        # SAVE TO SQLITE CRM
                        # ---------------------------------

                        save_report_to_database(
                            report
                        )

                        st.session_state[
                            "bulk_report"
                        ] = report


                    st.success(
                        "Customer analysis completed "
                        "and saved to CRM."
                    )


        except Exception as error:

            st.error(
                f"Unable to process uploaded file: {error}"
            )


    # -------------------------------------------------
    # SHOW BULK RESULTS
    # -------------------------------------------------

    if "bulk_report" in st.session_state:

        report = st.session_state[
            "bulk_report"
        ]

        st.divider()

        st.subheader(
            "📊 Churn Risk Summary"
        )


        # ---------------------------------------------
        # COUNTS
        # ---------------------------------------------

        high_count = (
            report["risk_level"]
            .eq("High")
            .sum()
        )

        medium_count = (
            report["risk_level"]
            .eq("Medium")
            .sum()
        )

        low_count = (
            report["risk_level"]
            .eq("Low")
            .sum()
        )


        col1, col2, col3, col4 = (
            st.columns(4)
        )

        with col1:

            st.metric(
                "Total Customers",
                len(report),
            )

        with col2:

            st.metric(
                "🔴 High Risk",
                high_count,
            )

        with col3:

            st.metric(
                "🟠 Medium Risk",
                medium_count,
            )

        with col4:

            st.metric(
                "🟢 Low Risk",
                low_count,
            )


        # ---------------------------------------------
        # CHART
        # ---------------------------------------------

        st.subheader(
            "Churn Risk Distribution"
        )

        chart_data = pd.DataFrame(
            {
                "Risk Level": [
                    "High",
                    "Medium",
                    "Low",
                ],
                "Customers": [
                    high_count,
                    medium_count,
                    low_count,
                ],
            }
        ).set_index(
            "Risk Level"
        )

        st.bar_chart(
            chart_data
        )


        # ---------------------------------------------
        # RESULTS TABLE
        # ---------------------------------------------

        st.subheader(
            "CRM Analysis Results"
        )

        st.dataframe(
            report,
            width="stretch",
        )


        # ---------------------------------------------
        # HIGH RISK FROM BULK UPLOAD
        # ---------------------------------------------

        st.subheader(
            "🚨 High-Risk Customers"
        )

        bulk_high_risk = report[
            report["risk_level"] == "High"
        ]

        if bulk_high_risk.empty:

            st.success(
                "No high-risk customers found "
                "in this upload."
            )

        else:

            st.dataframe(
                bulk_high_risk[
                    [
                        "customer_id",
                        "customer_name",
                        "recent_message",
                        "sentiment",
                        "matched_signals",
                        "risk_score",
                        "retention_action",
                    ]
                ],
                width="stretch",
                hide_index=True,
            )


        # ---------------------------------------------
        # DOWNLOAD REPORT
        # ---------------------------------------------

        output_csv = (
            report
            .to_csv(index=False)
            .encode("utf-8")
        )

        st.download_button(
            label="⬇️ Download Churn Report",
            data=output_csv,
            file_name="churn_report.csv",
            mime="text/csv",
        )


# =================================================
# TAB 3 - CRM RETENTION DASHBOARD
# =================================================

with dashboard_tab:

    st.subheader(
        "📊 CRM Retention Dashboard"
    )


    try:

        crm_data = get_all_customers()


        if crm_data.empty:

            st.info(
                "No CRM records available yet. "
                "Analyze customer messages first."
            )

        else:

            # -----------------------------------------
            # COUNTS
            # -----------------------------------------

            total_customers = len(
                crm_data
            )

            high_count = (
                crm_data["risk_level"]
                .eq("High")
                .sum()
            )

            medium_count = (
                crm_data["risk_level"]
                .eq("Medium")
                .sum()
            )

            low_count = (
                crm_data["risk_level"]
                .eq("Low")
                .sum()
            )


            col1, col2, col3, col4 = (
                st.columns(4)
            )

            with col1:

                st.metric(
                    "Customers",
                    total_customers,
                )

            with col2:

                st.metric(
                    "🔴 High Risk",
                    high_count,
                )

            with col3:

                st.metric(
                    "🟠 Medium Risk",
                    medium_count,
                )

            with col4:

                st.metric(
                    "🟢 Low Risk",
                    low_count,
                )


            st.divider()


            # -----------------------------------------
            # CRM RISK DISTRIBUTION
            # -----------------------------------------

            st.subheader(
                "CRM Risk Distribution"
            )

            db_summary = get_risk_summary()

            if not db_summary.empty:

                summary_chart = (
                    db_summary
                    .set_index(
                        "risk_level"
                    )
                )

                st.bar_chart(
                    summary_chart
                )


            # -----------------------------------------
            # PRIORITY RETENTION QUEUE
            # -----------------------------------------

            st.subheader(
                "🚨 Priority Retention Queue"
            )

            high_risk_customers = (
                get_high_risk_customers()
            )

            if high_risk_customers.empty:

                st.success(
                    "No high-risk customers "
                    "currently require follow-up."
                )

            else:

                st.dataframe(
                    high_risk_customers,
                    width="stretch",
                    hide_index=True,
                )


            # -----------------------------------------
            # ALL CRM RECORDS
            # -----------------------------------------

            st.subheader(
                "All CRM Customer Records"
            )

            st.dataframe(
                crm_data,
                width="stretch",
                hide_index=True,
            )


            # -----------------------------------------
            # DOWNLOAD CRM REPORT
            # -----------------------------------------

            crm_csv = (
                crm_data
                .to_csv(index=False)
                .encode("utf-8")
            )

            st.download_button(
                label=(
                    "⬇️ Download CRM Retention Report"
                ),
                data=crm_csv,
                file_name=(
                    "crm_retention_report.csv"
                ),
                mime="text/csv",
            )


    except Exception as error:

        st.error(
            f"Unable to load CRM dashboard: {error}"
        )


# =================================================
# FOOTER
# =================================================

st.divider()

st.caption(
    "Customer Churn Text Signal Detector | "
    "Python • pandas • NLTK/VADER • SQLite • Streamlit"
)
