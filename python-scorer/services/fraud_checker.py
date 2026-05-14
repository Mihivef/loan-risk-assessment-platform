"""
Fraud Detection Service

Simulates a real-time fraud detection model.
In production this would:
  - Query a feature store for historical applicant behaviour
  - Run an isolation forest or gradient boosting model
  - Check against a sanctions/blacklist database
  - Apply velocity rules (how many applications in last 30 days)
"""

from models.schemas import FraudCheckRequest, FraudCheckResponse
from typing import List


SUSPICIOUS_EMPLOYERS = {"abc pvt ltd", "xyz corp", "fake company", "test employer"}

DISPOSABLE_DOMAINS = {"mailinator.com", "tempmail.com", "guerrillamail.com", "throwaway.email"}


def check_fraud(req: FraudCheckRequest) -> FraudCheckResponse:
    """
    Run fraud checks on the applicant's profile.
    Returns a fraud probability (0–1) and list of flags.
    """
    flags: List[str] = []
    fraud_score = 0.0


    if req.annual_income > 0:
        ratio = req.requested_amount / req.annual_income
        if ratio > 10:
            flags.append("requested_amount_exceeds_10x_income")
            fraud_score += 0.30
        elif ratio > 7:
            flags.append("requested_amount_exceeds_7x_income")
            fraud_score += 0.15

    if req.employer_name.lower().strip() in SUSPICIOUS_EMPLOYERS:
        flags.append("employer_on_watchlist")
        fraud_score += 0.35

    domain = req.applicant_email.split("@")[-1].lower() if "@" in req.applicant_email else ""
    if domain in DISPOSABLE_DOMAINS:
        flags.append("disposable_email_domain")
        fraud_score += 0.25

    phone = req.applicant_phone.strip().replace(" ", "").replace("-", "")
    if len(phone) != 10 or not phone.isdigit():
        flags.append("invalid_phone_format")
        fraud_score += 0.10
    if len(set(phone)) <= 2 and phone.isdigit():
        flags.append("suspicious_phone_pattern")
        fraud_score += 0.20

    if req.annual_income % 100000 == 0 and req.annual_income >= 1000000:
        flags.append("suspiciously_round_income_figure")
        fraud_score += 0.05

    fraud_score = round(min(fraud_score, 1.0), 4)
    is_suspicious = fraud_score >= 0.25

    return FraudCheckResponse(
        application_id=req.application_id,
        fraud_probability=fraud_score,
        is_suspicious=is_suspicious,
        flags=flags,
    )
