import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python-scorer'))
 
from models.schemas import CreditScoreRequest, RiskBand
from services.credit_scorer import( 
    score_credit_risk,
    _score_cibil,
    _score_dti,
    _score_employment,
    _score_income_ratio,
    _score_tenure,
    _estimate_emi,
    _score_to_band
)

def test_cibil_score_():
    risk_factors = []
    score = _score_cibil(850, risk_factors)

    assert score > 0.9
    assert risk_factors == []

def test_cibil_score_should_return_expected_score():
    risk_factors = []
    score = _score_cibil(650, risk_factors)

    expected = (650 - 300) / 600
    assert score == pytest.approx(expected, rel=1e-2)

    assert risk_factors == []

def test_cibil_score_should_return_zero_for_low_score():
    risk_factors = []
    score = _score_cibil(300, risk_factors)

    assert score == 0
    assert "low CIBIL score (300)" in risk_factors

def test_cibil_score_should_return_zero_for_below_min():
    risk_factors = []
    score = _score_cibil(200, risk_factors)

    assert score == 0
    assert "low CIBIL score (200)" in risk_factors

def test_cibil_score_should_return_one_for_above_max():
    risk_factors = []
    score = _score_cibil(900, risk_factors)

    assert score == 1
    assert risk_factors == []

    assert score == 1
def test_estimate_emi_normal():
    emi = _estimate_emi(
        principal=100000,
        annual_rate=12,
        months=12
    )

    assert emi > 8000
    assert emi < 10000

def test_estimate_emi_should_return_expected_emi_for_zero_interest():
    emi = _estimate_emi(
        principal=120000,
        annual_rate=0,
        months=12
    )

    assert emi == 10000

def test_estimate_emi_should_return_zero_for_zero_principal():
    emi = _estimate_emi(
        principal=0,
        annual_rate=12,
        months=12
    )

    assert emi == 0

def test_estimate_emi_should_return_expected_emi_for_one_month():
    emi = _estimate_emi(
        principal=100000,
        annual_rate=12,
        months=1
    )

    assert emi > 100000

def test_dti_should_return_expected_dti_and_score():
    risk_factors = []

    dti, score = _score_dti(
        annual_income=1200000,
        requested_amount=100000,
        existing_emis=5000,
        risk_factors=risk_factors
    )

    assert dti < 0.5
    assert score > 0
    assert len(risk_factors) == 0

def test_dti_high_should_return_expected_dti_and_score():
    risk_factors = []

    dti, score = _score_dti(
        annual_income=300000,
        requested_amount=1000000,
        existing_emis=30000,
        risk_factors=risk_factors
    )

    assert dti > 0.5
    assert score >= 0
    assert any("debt-to-income ratio" in x for x in risk_factors)

def test_dti_should_return_one_when_zero_income():
    risk_factors = []

    dti, score = _score_dti(
        annual_income=0,
        requested_amount=100000,
        existing_emis=0,
        risk_factors=risk_factors
    )

    assert dti == 1.0
    assert score == 0

def test_dti_should_return_at_least_zero_when_positive_income_at_boundary():
    risk_factors = []

    dti, score = _score_dti(
        annual_income=600000,
        requested_amount=500000,
        existing_emis=10000,
        risk_factors=risk_factors
    )

    assert score >= 0

def test_employment_should_return_one_when_salaried():
    risk_factors = []
    score = _score_employment("salaried", risk_factors)

    assert score == 1.0
    assert risk_factors == []

def test_employment_should_return_expected_when_business_owner():
    risk_factors = []
    score = _score_employment("business_owner", risk_factors)

    assert score == 0.75


def test_employment_should_return_expected_when_self_employed():
    risk_factors = []
    score = _score_employment("self_employed", risk_factors)

    assert score == 0.55
    assert "self-employed (variable income)" in risk_factors

def test_employment_should_return_expected_when_freelancer():
    risk_factors = []
    score = _score_employment("freelancer", risk_factors)

    assert score == 0.5

def test_income_ratio_should_return_score_as_1():
    risk_factors = []

    score = _score_income_ratio(
        annual_income=1000000,
        requested_amount=200000,
        risk_factors=risk_factors
    )

    assert score == 1.0
    assert risk_factors == []

def test_income_ratio_should_return_expected_when_high_requested_amount():
    risk_factors = []

    score = _score_income_ratio(
        annual_income=300000,
        requested_amount=1200000,
        risk_factors=risk_factors
    )

    assert score < 1
    assert "high loan-to-income ratio" in risk_factors

def test_income_ratio_should_return_expected_when_extreme_requested_amount():
    risk_factors = []

    score = _score_income_ratio(
        annual_income=200000,
        requested_amount=2000000,
        risk_factors=risk_factors
    )

    assert score < 0.5
    assert "requested amount exceeds 5x annual income" in risk_factors

def test_income_ratio_should_return_one_when_zero_requested():
    risk_factors = []

    score = _score_income_ratio(
        annual_income=1000000,
        requested_amount=0,
        risk_factors=risk_factors
    )

    assert score == 1.0

def test_tenure_should_return_one_when_above_five_years():
    risk_factors = []
    score = _score_tenure(6, risk_factors)

    assert score == 1.0

def test_tenure_should_return_less_than_one_when_less_than_one_year():
    risk_factors = []
    score = _score_tenure(0.5, risk_factors)

    assert score < 1
    assert "less than 1 year in current employment" in risk_factors

def test_tenure_should_return_expected_when_between_one_and_two():
    risk_factors = []
    score = _score_tenure(1.5, risk_factors)

    assert "low employment tenure (< 2 years)" in risk_factors

def test_tenure_should_return_zero_when_zero_years():
    risk_factors = []
    score = _score_tenure(0, risk_factors)

    assert score == 0

def test_band_should_return_low():
    assert _score_to_band(0.75) == RiskBand.LOW

def test_band_should_return_medium():
    assert _score_to_band(0.55) == RiskBand.MEDIUM

def test_band_should_return_high():
    assert _score_to_band(0.35) == RiskBand.HIGH

def test_band_should_return_very_high():
    assert _score_to_band(0.34) == RiskBand.VERY_HIGH

def test_credit_score_best_case():
    req = CreditScoreRequest(
        application_id=1,
        cibil_score=850,
        annual_income=2000000,
        requested_amount=100000,
        existing_monthly_emis=0,
        employment_type="salaried",
        years_employed=10,
        loan_type="personal"
    )

    result = score_credit_risk(req)

    assert result.risk_band == RiskBand.LOW
    assert result.ml_credit_score > 0.8

def test_credit_score_should_return_the_expected_mlcreditscore_when_borderline():
    req = CreditScoreRequest(
        application_id=3,
        cibil_score=700,
        annual_income=600000,
        requested_amount=500000,
        existing_monthly_emis=10000,
        employment_type="business_owner",
        years_employed=2,
        loan_type="personal"
    )

    result = score_credit_risk(req)

    assert 0 <= result.ml_credit_score <= 1
def test_credit_score_should_return_the_expected_mlcreditscore_when_zero_income():
    req = CreditScoreRequest(
        application_id=4,
        cibil_score=750,
        annual_income=0,
        requested_amount=100000,
        existing_monthly_emis=0,
        employment_type="salaried",
        years_employed=3,
        loan_type="personal"
    )

    result = score_credit_risk(req)

    assert result.debt_to_income_ratio == 1.0

def test_credit_score_should_return_the_expected_mlcreditscore_when_unknown_employment():
    req = CreditScoreRequest(
        application_id=5,
        cibil_score=750,
        annual_income=1000000,
        requested_amount=100000,
        existing_monthly_emis=0,
        employment_type="freelancer",
        years_employed=3,
        loan_type="personal"
    )

    result = score_credit_risk(req)

    assert result.ml_credit_score > 0
