from fastapi import APIRouter, HTTPException
from models.schemas import (
    CreditScoreRequest, CreditScoreResponse,
    FraudCheckRequest,  FraudCheckResponse,
)
from services.credit_scorer import score_credit_risk
from services.fraud_checker  import check_fraud
from db.database import log_credit_score, log_fraud_check, get_score_history

router = APIRouter()


@router.post("/score/credit-risk", response_model=CreditScoreResponse)
async def credit_risk_endpoint(req: CreditScoreRequest):
  
    try:
        result = score_credit_risk(req)

        try:
            await log_credit_score(
                req.application_id,
                result.ml_credit_score,
                result.risk_band.value,
                result.risk_factors,
                result.debt_to_income_ratio,
                result.confidence,
            )
        except Exception as db_err:
            print(f"DB log failed (non-fatal): {db_err}")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scoring failed: {e}")


@router.post("/score/fraud-check", response_model=FraudCheckResponse)
async def fraud_check_endpoint(req: FraudCheckRequest):

    try:
        result = check_fraud(req)

        try:
            await log_fraud_check(
                req.application_id,
                result.fraud_probability,
                result.flags,
            )
        except Exception as db_err:
            print(f"DB log failed (non-fatal): {db_err}")

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fraud check failed: {e}")


@router.get("/score/factors/{app_id}")
async def get_score_factors(app_id: int):

    history = []
    try:
        history = await get_score_history(app_id)
    except Exception:
        pass 

    return {
        "application_id": app_id,
        "model_version": "v1.3.0",
        "feature_weights": {
            "cibil_score":       "35% — primary creditworthiness signal",
            "debt_to_income":    "25% — total obligation vs income",
            "employment_type":   "15% — income stability indicator",
            "income_loan_ratio": "15% — affordability check",
            "employment_tenure": "10% — job stability indicator",
        },
        "risk_bands": {
            "LOW":       "score >= 0.75 — eligible for best rates",
            "MEDIUM":    "score 0.55–0.74 — standard rates apply",
            "HIGH":      "score 0.35–0.54 — higher rates, may need collateral",
            "VERY_HIGH": "score < 0.35 — likely rejected by policy engine",
        },
        "score_history": history,
    }
