# Customer Churn Text Signal Detector

## Project Overview

The Customer Churn Text Signal Detector is a beginner-level CRM and NLP project built using Python, pandas, NLTK/VADER, keyword rules, SQLite, and Streamlit.

The system analyzes recent customer messages to identify dissatisfaction, cancellation intent, and switching signals. It then assigns a churn-risk level and recommends a retention follow-up action.

## Project Objective

The objective of this project is to identify possible customer churn signals from recent customer messages and convert those signals into CRM-friendly risk flags.

## Workflow

```text
Customer History
      ↓
Analyze Messages
      ↓
Sentiment Analysis
      +
Keyword Signals
      ↓
Risk Score
      ↓
Low / Medium / High Risk
      ↓
Retention Follow-up
      ↓
SQLite CRM Database