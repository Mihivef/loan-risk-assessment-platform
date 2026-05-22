from pydantic import BaseModel
from typing import List
from enum import Enum


class RiskBand(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"



class CreditScoreRequest(BaseModel):
    application_id: int
    annual_income: float
    existing_monthly_emis: float
    employment_type: str         
    years_employed: float
    cibil_score: int              
    requested_amount: float
    loan_type: str


class FraudCheckRequest(BaseModel):
    application_id: int
    applicant_email: str
    applicant_phone: str
    annual_income: float
    requested_amount: float
    employer_name: str



class CreditScoreResponse(BaseModel):
    application_id: int
    ml_credit_score: float        
    risk_band: RiskBand
    risk_factors: List[str]
    debt_to_income_ratio: float
    confidence: float


class FraudCheckResponse(BaseModel):
    application_id: int
    fraud_probability: float      
    is_suspicious: bool
    flags: List[str]
