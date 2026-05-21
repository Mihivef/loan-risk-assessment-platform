from models.schemas import CreditScoreRequest, CreditScoreResponse, RiskBand
from typing import List, Tuple


WEIGHTS = {
    "cibil":        0.35,   
    "dti":          0.25,   
    "employment":   0.15,   
    "income_ratio": 0.15,  
    "tenure":       0.10,   
}


def score_credit_risk(req: CreditScoreRequest) -> CreditScoreResponse:
    risk_factors: List[str] = []
    cibil_score=_score_cibil(req.cibil_score, risk_factors)
    dti,dti_score=_score_dti(
        req.annual_income,
        req.requested_amount,
        req.existing_monthly_emis,
        risk_factors,
    )
    employment_score = _score_employment(req.employment_type, risk_factors)

    income_ratio_score = _score_income_ratio(
        req.annual_income,
        req.requested_amount,
        risk_factors
    )
    tenure_score = _score_tenure(req.years_employed, risk_factors)
    ml_score=_calculate_final_score(
        cibil_score,
        dti_score,
        employment_score,
        income_ratio_score,
        tenure_score
    )
    return CreditScoreResponse(
        application_id=req.application_id,
        ml_credit_score=ml_score,
        risk_band=_score_to_band(ml_score),
        risk_factors=risk_factors,
        debt_to_income_ratio=round(dti, 4),
        confidence=0.87,
    )

def _score_cibil(cibil: int, risk_factors: List[str]) -> float:
    score = (cibil - 300) / 600.0

    if cibil < 650:
        risk_factors.append(f"low CIBIL score ({cibil})")

    return max(0, min(score, 1))

def _score_dti(annual_income: float, requested_amount: float, existing_emis: float, risk_factors: List[str]) -> Tuple[float,float]:
    monthly_income = annual_income / 12 
    projected_emi = _estimate_emi(requested_amount,12.0,36)

    total_emi= existing_emis + projected_emi
    dti = total_emi / monthly_income if monthly_income > 0 else 1

    score=max(0,1 -(dti/0.6))

    if dti>0.5:
        risk_factors.append(f"high debt-to-income ratio ({dti:.1%})")
    elif dti>0.3:
        risk_factors.append(f"elevated debt-to-income ratio ({dti:.1%})")
    return dti,score


def _score_employment(employment_type: str, risk_factors: List[str]) -> float:
    employment_map = {
        "salaried": 1.0,
        "business_owner": 0.75,
        "self_employed": 0.55
    }

    score = employment_map.get(employment_type, 0.5)

    if employment_type == "self_employed":
        risk_factors.append("self-employed (variable income)")

    return score


def _score_income_ratio(
    annual_income: float,
    requested_amount: float,
    risk_factors: List[str]
) -> float:

    ratio_score = min(annual_income / max(requested_amount, 1), 2.0) / 2.0

    if requested_amount > annual_income * 5:
        risk_factors.append("requested amount exceeds 5x annual income")
    elif requested_amount > annual_income * 3:
        risk_factors.append("high loan-to-income ratio")

    return ratio_score


def _score_tenure(years_employed: float, risk_factors: List[str]) -> float:
    score = min(years_employed / 5.0, 1.0)

    if years_employed < 1:
        risk_factors.append("less than 1 year in current employment")
    elif years_employed < 2:
        risk_factors.append("low employment tenure (< 2 years)")

    return score


def _calculate_final_score(
    cibil: float,
    dti: float,
    employment: float,
    income_ratio: float,
    tenure: float
) -> float:

    score = (
        WEIGHTS["cibil"] * cibil +
        WEIGHTS["dti"] * dti +
        WEIGHTS["employment"] * employment +
        WEIGHTS["income_ratio"] * income_ratio +
        WEIGHTS["tenure"] * tenure
    )

    return round(max(0.0, min(1.0, score)), 4)




def _score_to_band(score: float) -> RiskBand:
    if score >= 0.75:
        return RiskBand.LOW
    elif score >= 0.55:
        return RiskBand.MEDIUM
    elif score >= 0.35:
        return RiskBand.HIGH
    return RiskBand.VERY_HIGH


def _estimate_emi(principal: float, annual_rate: float, months: int) -> float:
    r = annual_rate / 12 / 100

    if r == 0:
        return principal / months

    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)
  



    