# Customer Churn Text Signal Detector

An English-language, rule-based tool that extracts cancellation, switching, and dissatisfaction signals from customer messages. VADER provides sentiment; explicit text signals determine retention priority. Risk scores are heuristic points, not churn probabilities or a trained predictive model.

## Run locally

Use Python 3.12 and a virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

VADER needs the NLTK `vader_lexicon` resource. The first analysis import downloads it if missing, so first-time setup requires internet access. In this workspace, the verified environment is `.venv-1`.

## Scoring policy

- Active cancellation or refusal to renew: 3 points.
- Switching language: 2 points; explicit commitment such as “I am switching” receives 3.
- Active dissatisfaction: 1 point, plus 1 for negative or 2 for strongly negative sentiment in that complaint clause.
- High: 3 or more points. Medium: 1–2 points. Low: 0 points.

Conditional cancellation threats are High because they warrant immediate follow-up. Positive language does not override an active cancellation request. Negated signals, internal plan changes, and cancellation of appointments or orders are excluded by context rules. Sentiment alone does not establish churn risk. Low means no active signal was detected, not a guarantee that the customer will stay.

Examples:

| Message | Expected risk |
| --- | --- |
| Please cancel my subscription. | High |
| I do not want to cancel my subscription. | Low |
| I will not renew my subscription. | High |
| I am switching to another provider. | High |
| I may switch to another provider. | Medium |
| The service is too expensive. | Medium |
| Please switch to dark mode. | Low |
| I contacted support and they solved my problem. | Low |

## CSV and CRM workflow

Upload a CSV with `recent_message`; include stable `customer_id` and `customer_name` values for CRM records. Blank, missing, numeric-only, and punctuation-only messages are rejected instead of being labeled Low. Batch validation happens before saving. Reanalyzing an exported report replaces its old prediction columns. Customer IDs are read as text to preserve leading zeros.

The app saves bulk results in local `churn.db`. Existing customer IDs are updated, so use unique and stable IDs. Single-message results must be analyzed again after any input changes. Upload changes clear the previous bulk report.

For CSV-only processing:

```powershell
.\.venv\Scripts\python.exe churn_analyzer.py
```

This reads `customer_messages.csv` and writes `churn_report.csv`. Running `database.py` also saves these records to SQLite and exports `crm_retention_report.csv`.

## Verification

```powershell
.\.venv-1\Scripts\python.exe -m unittest -v
```

Tests cover negation, word boundaries, plan changes, renewal refusal, mixed sentiment, invalid input, replacement of stale report columns, CSV/SQLite round trips, and Streamlit analysis/edit/save behavior. Tests use temporary CRM databases.

## Limits

These are deterministic English phrase and context rules. Sarcasm, quoted statements, third-party references, long-distance negation, historical intent, and unfamiliar wording can still be misclassified. No labeled evaluation dataset or evaluator's failing examples were supplied, so the regression tests do not establish real-world accuracy. Review flagged messages before contacting customers. Existing stored CRM results and exported reports must be reanalyzed to use the updated rules.
