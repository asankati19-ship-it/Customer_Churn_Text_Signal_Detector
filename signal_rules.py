"""Transparent English rules for current customer churn signals.

These rules flag evidence, not a calibrated probability of future churn.
"""

import re
import unicodedata


def normalize(text):
    text = unicodedata.normalize("NFKC", text).lower().replace("’", "'")
    for short, expanded in {
        "don't": "do not", "doesn't": "does not", "didn't": "did not",
        "won't": "will not", "wouldn't": "would not", "can't": "cannot",
        "isn't": "is not", "wasn't": "was not", "i'm": "i am",
    }.items():
        text = text.replace(short, expanded)
    return re.sub(r"\s+", " ", text).strip()


def clauses(text):
    return [part.strip() for part in re.split(
        r"[.!?;\n]+|\b(?:but|however|although|yet)\b", normalize(text)
    ) if part.strip()]


def is_negated(text, start):
    # Negation must modify this intent, not an unrelated earlier complaint.
    prefix = re.split(r"[.!?;,]|\b(?:but|however|yet|and)\b", text[:start])[-1]
    prefix = re.sub(r"\bnot only\b", "", prefix)
    intent = r"(?:(?:want|wish|plan|intend|need)\s+to\s+|(?:going|planning)\s+to\s+)?"
    destination = r"(?:(?:switch(?:ing|ed)?|mov(?:e|ing))\s+to\s+(?:(?:a|another|the)\s+)?)?"
    return bool(re.search(
        r"\b(?:not|never|no longer|no|without)\s+" + intent + destination + r"$",
        prefix,
    ))


def matches(text, keywords):
    found = []
    for keyword in sorted(keywords, key=len, reverse=True):
        if any(keyword in existing for existing in found):
            continue
        for match in re.finditer(r"(?<!\w)" + re.escape(keyword) + r"(?!\w)", text):
            if not is_negated(text, match.start()):
                found.append(keyword)
                break
    return found


def departure_signals(clause):
    cancellation = []
    switching = []
    # A cancellation of a meeting, order, or support ticket is not account churn.
    cancel_pattern = r"\b(?:cancel(?:ling|ing|led|ed)?|terminate|unsubscribe|close my account|stop my service|remove my account)\b"
    for match in re.finditer(cancel_pattern, clause):
        tail = clause[match.end():]
        if is_negated(clause, match.start()):
            continue
        if re.match(r"\s+(?:(?:my|the|a|this|our)\s+)?(?:order|meeting|appointment|ticket|request|download|upload|email|newsletter|notification)\b", tail):
            continue
        end = re.match(r"\s+(?:(?:my|the|our)\s+)?(?:subscription|account|service|membership|plan)\b", tail)
        cancellation.append(clause[match.start():match.end() + (end.end() if end else 0)])

    for pattern in (
        r"\b(?:do not|will not|not going to|no longer want to) renew\b",
        r"\b(?:do not want to continue|stop renewing|stop using (?:your|the) service)\b",
    ):
        cancellation.extend(m.group() for m in re.finditer(pattern, clause))

    for match in re.finditer(r"\b(?:switch(?:ing|ed)?|moving|move|leaving|leave|want to leave|another provider|another company|competitor)\b", clause):
        if is_negated(clause, match.start()):
            continue
        tail = clause[match.end():]
        if re.match(r"\s+(?:to\s+)?(?:(?:a|the|my|your|another)\s+)?(?:plan|tier|annual|monthly|dark|light|email|payment|address)\b", tail):
            continue
        if match.group() in {"moving", "move"} and not re.search(r"\b(?:provider|company|competitor|service)\b", tail):
            continue
        if match.group() in {"leave", "leaving"} and re.match(r"\s+(?:a|the|my)\s+(?:review|comment|message)\b", tail):
            continue
        switching.append(match.group())
    return cancellation, switching
