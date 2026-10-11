# Customer Churn Text Signal Detector
# Churn-risk keyword definitions

import nltk
import pandas as pd
from nltk.sentiment import SentimentIntensityAnalyzer


# =================================================
# CHURN SIGNAL KEYWORDS
# =================================================

CANCELLATION_KEYWORDS = [
    "cancel",
    "cancel my subscription",
    "close my account",
    "terminate",
    "stop my service",
    "remove my account",
    "unsubscribe",
    "do not want to continue",
]


DISSATISFACTION_KEYWORDS = [
    "unhappy",
    "terrible",
    "disappointed",
    "frustrated",
    "not satisfied",
    "awful",
    "too expensive",
    "too high",
    "money back",
    "refund",
    "repeated problems",
    "keeps crashing",
    "nobody has fixed",
    "not fixed",
    "contacted support",
    "expected better",
    "slow recently",
]


SWITCHING_KEYWORDS = [
    "switch",
    "switching providers",
    "another provider",
    "another company",
    "competitor",
    "want to leave",
    "moving to another",
]


POSITIVE_CONTEXT_PHRASES = [
    "no complaints",
    "no issues",
    "very happy",
    "working perfectly",
    "working well",
    "very helpful",
    "excellent",
    "satisfied now",
    "resolved my issue",
    "solved my problem",
    "everything is fine",
]


# =================================================
# VADER SENTIMENT ANALYZER
# =================================================

def get_sentiment_analyzer():
    """
    Load VADER sentiment analyzer.
    Download the vader_lexicon automatically if needed.
    """

    try:
        return SentimentIntensityAnalyzer()

    except LookupError:
        nltk.download("vader_lexicon", quiet=True)
        return SentimentIntensityAnalyzer()


sia = get_sentiment_analyzer()


# =================================================
# KEYWORD MATCHING
# =================================================

def find_keywords(message, keywords):
    """
    Find matching keywords or phrases in a customer message.

    Longer phrases are preferred so duplicate results such as
    'cancel' and 'cancel my subscription' are reduced.
    """

    text = str(message).lower()

    matches = [
        keyword
        for keyword in keywords
        if keyword in text
    ]

    # Sort longest phrases first
    matches.sort(key=len, reverse=True)

    filtered_matches = []

    for keyword in matches:

        if not any(
            keyword in existing
            for existing in filtered_matches
        ):
            filtered_matches.append(keyword)

    return filtered_matches


# =================================================
# SENTIMENT LABEL
# =================================================

def get_sentiment_label(compound_score):
    """
    Convert VADER compound score into
    Positive, Negative, or Neutral.
    """

    if compound_score >= 0.05:
        return "Positive"

    elif compound_score <= -0.05:
        return "Negative"

    else:
        return "Neutral"


# =================================================
# CUSTOMER MESSAGE ANALYSIS
# =================================================

def analyze_message(message):
    """
    Analyze one customer message and return:
    - sentiment score
    - sentiment label
    - matched churn signals
    - risk score
    - risk level
    - retention action
    """

    if pd.isna(message):
        message = ""

    message = str(message)

    # ---------------------------------------------
    # SENTIMENT ANALYSIS
    # ---------------------------------------------

    sentiment_scores = sia.polarity_scores(message)

    compound_score = sentiment_scores["compound"]

    sentiment_label = get_sentiment_label(
        compound_score
    )


    # ---------------------------------------------
    # KEYWORD DETECTION
    # ---------------------------------------------

    cancellation_matches = find_keywords(
        message,
        CANCELLATION_KEYWORDS,
    )

    dissatisfaction_matches = find_keywords(
        message,
        DISSATISFACTION_KEYWORDS,
    )

    switching_matches = find_keywords(
        message,
        SWITCHING_KEYWORDS,
    )

    positive_context_matches = find_keywords(
        message,
        POSITIVE_CONTEXT_PHRASES,
    )


    # ---------------------------------------------
    # RISK SCORE
    # ---------------------------------------------

    risk_score = 0


    # Explicit cancellation is strongest signal
    if cancellation_matches:
        risk_score += 3


    # Switching / competitor language
    if switching_matches:
        risk_score += 2


    # Dissatisfaction signal
    if dissatisfaction_matches:
        risk_score += 1


    # Check whether churn signals exist
    has_churn_signal = bool(
        cancellation_matches
        or dissatisfaction_matches
        or switching_matches
    )


    # Check positive context
    positive_context = bool(
        positive_context_matches
    )


    # ---------------------------------------------
    # SENTIMENT CONTRIBUTION
    # ---------------------------------------------

    # Prevent false risk from sentences such as:
    # "Everything is fine. No issues so far."
    #
    # However, if an explicit churn keyword exists,
    # sentiment can still contribute to the score.

    if not (
        positive_context
        and not has_churn_signal
    ):

        if compound_score <= -0.5:
            risk_score += 2

        elif compound_score < -0.05:
            risk_score += 1


    # ---------------------------------------------
    # FINAL RISK LEVEL
    # ---------------------------------------------

    if risk_score >= 3:
        risk_level = "High"

    elif risk_score >= 1:
        risk_level = "Medium"

    else:
        risk_level = "Low"


    # ---------------------------------------------
    # RETENTION ACTION
    # ---------------------------------------------

    if risk_level == "High":

        retention_action = (
            "Immediate retention follow-up"
        )

    elif risk_level == "Medium":

        retention_action = (
            "Contact customer and review concerns"
        )

    else:

        retention_action = (
            "No immediate retention action"
        )


    # ---------------------------------------------
    # COMBINE MATCHED CHURN SIGNALS
    # ---------------------------------------------

    all_matches = (
        cancellation_matches
        + dissatisfaction_matches
        + switching_matches
    )


    matched_signals = (
        ", ".join(all_matches)
        if all_matches
        else "None"
    )


    positive_context_text = (
        ", ".join(positive_context_matches)
        if positive_context_matches
        else "None"
    )


    # ---------------------------------------------
    # RETURN ANALYSIS RESULT
    # ---------------------------------------------

    return {
        "sentiment_score": round(
            compound_score,
            4,
        ),
        "sentiment": sentiment_label,
        "matched_signals": matched_signals,
        "positive_context": positive_context_text,
        "risk_score": risk_score,
        "risk_level": risk_level,
        "retention_action": retention_action,
    }


# =================================================
# PROCESS COMPLETE CUSTOMER DATASET
# =================================================

def process_customer_dataset(
    input_file="customer_messages.csv",
    output_file="churn_report.csv",
):
    """
    Read the customer message dataset,
    analyze every message,
    and save the final CRM churn report.
    """

    df = pd.read_csv(input_file)


    # Validate required column
    if "recent_message" not in df.columns:

        raise ValueError(
            "Input file must contain a 'recent_message' column."
        )


    # Analyze every customer message
    results = (
        df["recent_message"]
        .apply(analyze_message)
        .apply(pd.Series)
    )


    # Combine original data with NLP results
    report = pd.concat(
        [
            df.reset_index(drop=True),
            results.reset_index(drop=True),
        ],
        axis=1,
    )


    # Save final CRM report
    report.to_csv(
        output_file,
        index=False,
    )


    return report


# =================================================
# SUMMARY FUNCTION
# =================================================

def get_risk_summary(report):
    """
    Return counts of High, Medium, and Low risk customers.
    """

    summary = (
        report["risk_level"]
        .value_counts()
        .reindex(
            [
                "High",
                "Medium",
                "Low",
            ],
            fill_value=0,
        )
    )

    return summary


# =================================================
# RUN PROGRAM
# =================================================

if __name__ == "__main__":

    report = process_customer_dataset()


    # ---------------------------------------------
    # PRINT CUSTOMER ANALYSIS
    # ---------------------------------------------

    print(
        report[
            [
                "customer_id",
                "sentiment",
                "sentiment_score",
                "matched_signals",
                "risk_score",
                "risk_level",
                "retention_action",
            ]
        ].to_string(index=False)
    )


    # ---------------------------------------------
    # PRINT SUMMARY
    # ---------------------------------------------

    summary = get_risk_summary(report)

    print("\n-----------------------------------")
    print("CUSTOMER CHURN RISK SUMMARY")
    print("-----------------------------------")

    print(
        f"Total Customers: {len(report)}"
    )

    print(
        f"High Risk: {summary['High']}"
    )

    print(
        f"Medium Risk: {summary['Medium']}"
    )

    print(
        f"Low Risk: {summary['Low']}"
    )

    print(
        "\nChurn analysis completed successfully."
    )

    print(
        "CRM report saved as: churn_report.csv"
    )