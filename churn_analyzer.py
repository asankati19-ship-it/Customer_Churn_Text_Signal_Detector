# Customer Churn Text Signal Detector
# Churn-risk keyword definitions

import re

import nltk
from signal_rules import clauses, departure_signals, matches, normalize
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

    return matches(normalize(str(message)), keywords)


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

    if not isinstance(message, str) or not message.strip():
        raise ValueError("Customer message must be non-empty text.")
    if not any(character.isalpha() for character in message):
        raise ValueError("Customer message must contain words.")

    compound_score = sia.polarity_scores(message)["compound"]
    sentiment_label = get_sentiment_label(compound_score)
    cancellation_matches = []
    dissatisfaction_matches = []
    switching_matches = []
    positive_context_matches = []
    negative_contribution = 0
    committed_switch = False
    for clause in clauses(message):
        cancellation, switching = departure_signals(clause)
        # Support contact alone does not establish dissatisfaction.
        dissatisfaction = matches(clause, [
            word for word in DISSATISFACTION_KEYWORDS
            if word != "contacted support"
        ] + ["not working", "does not work", "poor service", "unreliable",
             "overcharged", "unresolved", "broken", "miserable"])
        positive = matches(clause, POSITIVE_CONTEXT_PHRASES)
        # Historical complaints followed by an explicit resolution are no longer active.
        resolved = bool(re.search(
            r"\b(?:resolved|solved|fixed)\b", clause
        )) and not bool(re.search(r"\b(?:not|never|unresolved|nobody|no one)\b", clause))
        if resolved:
            dissatisfaction = []
        cancellation_matches.extend(cancellation)
        switching_matches.extend(switching)
        dissatisfaction_matches.extend(dissatisfaction)
        positive_context_matches.extend(positive)
        if switching and re.search(r"\b(?:i am|we are|i will|we will|have decided to) (?:switch|mov|leav)", clause):
            committed_switch = True
        # Sentiment strengthens an active complaint; it cannot invent churn intent.
        if dissatisfaction:
            score = sia.polarity_scores(clause)["compound"]
            negative_contribution = max(negative_contribution, 2 if score <= -0.5 else 1 if score <= -0.05 else 0)

    cancellation_matches = list(dict.fromkeys(cancellation_matches))
    switching_matches = list(dict.fromkeys(switching_matches))
    dissatisfaction_matches = list(dict.fromkeys(dissatisfaction_matches))
    positive_context_matches = list(dict.fromkeys(positive_context_matches))
    risk_score = (
        (3 if cancellation_matches else 0)
        + (3 if committed_switch else 2 if switching_matches else 0)
        + (1 if dissatisfaction_matches else 0)
        + negative_contribution
    )

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

def analyze_dataframe(df):
    """Validate the whole batch before analysis; replace any stale result columns."""
    df = df.copy()
    df.columns = [str(column).strip().lower() for column in df.columns]
    if df.columns.duplicated().any():
        raise ValueError("CSV column names must be unique.")
    if "recent_message" not in df.columns:
        raise ValueError("Input file must contain a 'recent_message' column.")
    if df.empty:
        raise ValueError("Input file must contain at least one customer message.")
    results = []
    for position, message in enumerate(df["recent_message"], start=2):
        try:
            results.append(analyze_message(message))
        except ValueError as error:
            raise ValueError(f"CSV row {position}: {error}") from error
    analysis = pd.DataFrame(results)
    df = df.drop(columns=[column for column in analysis.columns if column in df])
    return pd.concat([df.reset_index(drop=True), analysis], axis=1)


def process_customer_dataset(
    input_file="customer_messages.csv",
    output_file="churn_report.csv",
):
    """
    Read the customer message dataset,
    analyze every message,
    and save the final CRM churn report.
    """

    df = pd.read_csv(input_file, dtype={"customer_id": str})
    report = analyze_dataframe(df)

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
