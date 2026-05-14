"""
Credit Risk Scoring Service

This simulates a real ML credit risk model using a weighted scoring formula.
In production, you would:
  - Load a trained scikit-learn / XGBoost model from disk
  - Call model.predict_proba(feature_vector) to get the risk score
  - Store model artifacts in MLflow or S3

The weights below are inspired by standard credit underwriting factors.
"""

from models.schemas import CreditScoreRequest, CreditScoreResponse, RiskBand
from typing import List, Tuple


WEIGHTS = {
    "cibil":        0.35,   # CIBIL score is the strongest signal in Indian lending
    "dti":          0.25,   # Debt-to-income ratio
    "employment":   0.15,   # Employment stability
    "income_ratio": 0.15,   # Income vs requested amount
    "tenure":       0.10,   # Employment tenure
}


def score_credit_risk(req: CreditScoreRequest) -> CreditScoreResponse:
    """
    Run the ML credit risk scoring model on the application.
    Returns a normalised score (0–1) and a risk band.
    """
    risk_factors: List[str] = []

    cibil_norm = (req.cibil_score - 300) / 600.0
    if req.cibil_score < 650:
        risk_factors.append(f"low CIBIL score ({req.cibil_score})")
    elif req.cibil_score < 700:
        risk_factors.append("below-average CIBIL score")

    monthly_income = req.annual_income / 12
    projected_emi = _estimate_emi(req.requested_amount, 12.0, 36)
    total_emi = req.existing_monthly_emis + projected_emi
    dti = total_emi / monthly_income if monthly_income > 0 else 1.0

    dti_score = max(0, 1 - (dti / 0.6))  # 60% DTI = worst score
    if dti > 0.5:
        risk_factors.append(f"high debt-to-income ratio ({dti:.1%})")
    elif dti > 0.4:
        risk_factors.append(f"elevated debt-to-income ratio ({dti:.1%})")

    employment_map = {"salaried": 1.0, "business_owner": 0.75, "self_employed": 0.55}
    employment_score = employment_map.get(req.employment_type, 0.5)
    if req.employment_type == "self_employed":
        risk_factors.append("self-employed (variable income)")

    income_ratio = min(req.annual_income / max(req.requested_amount, 1), 2.0) / 2.0
    if req.requested_amount > req.annual_income * 5:
        risk_factors.append("requested amount exceeds 5x annual income")
    elif req.requested_amount > req.annual_income * 3:
        risk_factors.append("high loan-to-income ratio")

    tenure_score = min(req.years_employed / 5.0, 1.0)  # 5+ years = full score
    if req.years_employed < 1:
        risk_factors.append("less than 1 year in current employment")
    elif req.years_employed < 2:
        risk_factors.append("low employment tenure (< 2 years)")

    ml_score = (
        WEIGHTS["cibil"]        * cibil_norm +
        WEIGHTS["dti"]          * dti_score +
        WEIGHTS["employment"]   * employment_score +
        WEIGHTS["income_ratio"] * income_ratio +
        WEIGHTS["tenure"]       * tenure_score
    )
    ml_score = round(max(0.0, min(1.0, ml_score)), 4)

    band = _score_to_band(ml_score)

    return CreditScoreResponse(
        application_id=req.application_id,
        ml_credit_score=ml_score,
        risk_band=band,
        risk_factors=risk_factors,
        debt_to_income_ratio=round(dti, 4),
        confidence=0.87,  # simulated model confidence
    )


def _score_to_band(score: float) -> RiskBand:
    if score >= 0.75:
        return RiskBand.LOW
    elif score >= 0.55:
        return RiskBand.MEDIUM
    elif score >= 0.35:
        return RiskBand.HIGH
    else:
        return RiskBand.VERY_HIGH


def _estimate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Reducing balance EMI formula — used internally for DTI estimation."""
    r = annual_rate / 12 / 100
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
