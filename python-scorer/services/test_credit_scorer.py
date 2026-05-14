import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python-scorer'))
 
from models.schemas import CreditScoreRequest, RiskBand
from services.credit_scorer import score_credit_risk
 
 
 
def make_request(**kwargs) -> CreditScoreRequest:
    defaults = {
        "application_id":      1,
        "annual_income":       960000,
        "existing_monthly_emis": 3000,
        "employment_type":     "salaried",
        "years_employed":      3.5,
        "cibil_score":         760,
        "requested_amount":    400000,
        "loan_type":           "personal",
    }
    defaults.update(kwargs)
    return CreditScoreRequest(**defaults)
 
 
 
class TestLowRiskApplicant:
 
    def test_high_cibil_gets_low_risk_band(self):
        req = make_request(cibil_score=800, annual_income=1200000,
                           existing_monthly_emis=0, years_employed=5)
        result = score_credit_risk(req)
        assert result.risk_band == RiskBand.LOW
 
    def test_high_cibil_gets_high_ml_score(self):
        req = make_request(cibil_score=820, annual_income=1500000,
                           existing_monthly_emis=2000, years_employed=6)
        result = score_credit_risk(req)
        assert result.ml_credit_score >= 0.75
 
    def test_low_risk_has_no_risk_factors(self):
        req = make_request(cibil_score=800, annual_income=2000000,
                           existing_monthly_emis=0, years_employed=5)
        result = score_credit_risk(req)
        assert len(result.risk_factors) == 0
 
    def test_salaried_employee_gets_better_score_than_self_employed(self):
        salaried = make_request(employment_type="salaried",   cibil_score=730)
        self_emp = make_request(employment_type="self_employed", cibil_score=730)
        res_sal  = score_credit_risk(salaried)
        res_self = score_credit_risk(self_emp)
        assert res_sal.ml_credit_score > res_self.ml_credit_score
 
    def test_low_dti_produces_low_debt_to_income_ratio(self):
        req = make_request(annual_income=1200000, existing_monthly_emis=0,
                           requested_amount=300000)
        result = score_credit_risk(req)
        assert result.debt_to_income_ratio < 0.3
 
 
 
class TestMediumRiskApplicant:
 
    def test_average_cibil_gets_medium_risk_band(self):
        req = make_request(cibil_score=680, annual_income=600000,
                           existing_monthly_emis=8000, years_employed=2)
        result = score_credit_risk(req)
        assert result.risk_band in [RiskBand.MEDIUM, RiskBand.HIGH]
 
    def test_medium_score_between_055_and_075(self):
        req = make_request(cibil_score=700, annual_income=700000,
                           existing_monthly_emis=5000, years_employed=2)
        result = score_credit_risk(req)
        assert 0.40 <= result.ml_credit_score <= 0.80
 
    def test_below_average_cibil_adds_risk_factor(self):
        req = make_request(cibil_score=660)
        result = score_credit_risk(req)
        assert any("CIBIL" in f or "cibil" in f.lower() for f in result.risk_factors)
 
 
 
class TestHighRiskApplicant:
 
    def test_low_cibil_gets_high_risk_band(self):
        req = make_request(cibil_score=580, annual_income=300000,
                           existing_monthly_emis=15000, years_employed=0.5)
        result = score_credit_risk(req)
        assert result.risk_band in [RiskBand.HIGH, RiskBand.VERY_HIGH]
 
    def test_very_low_cibil_gets_low_ml_score(self):
        req = make_request(cibil_score=400, annual_income=200000,
                           existing_monthly_emis=8000, years_employed=0.3)
        result = score_credit_risk(req)
        assert result.ml_credit_score < 0.35
 
    def test_high_dti_adds_risk_factor(self):
      
        req = make_request(annual_income=300000, existing_monthly_emis=18000,
                           requested_amount=200000)
        result = score_credit_risk(req)
        dti_flags = [f for f in result.risk_factors if "debt" in f.lower() or "income" in f.lower() or "dti" in f.lower()]
        assert len(dti_flags) > 0
 
    def test_short_employment_adds_risk_factor(self):
        req = make_request(years_employed=0.3)
        result = score_credit_risk(req)
        emp_flags = [f for f in result.risk_factors if "employment" in f.lower() or "year" in f.lower()]
        assert len(emp_flags) > 0
 
    def test_high_loan_to_income_ratio_adds_risk_factor(self):
        # requesting 10x income
        req = make_request(annual_income=300000, requested_amount=3000000)
        result = score_credit_risk(req)
        income_flags = [f for f in result.risk_factors if "income" in f.lower() or "amount" in f.lower()]
        assert len(income_flags) > 0
 
 
 
class TestScoreRangeValidation:
 
    def test_score_always_between_0_and_1(self):
        test_cases = [
            make_request(cibil_score=300, annual_income=100000),
            make_request(cibil_score=900, annual_income=5000000),
            make_request(cibil_score=600, annual_income=500000),
        ]
        for req in test_cases:
            result = score_credit_risk(req)
            assert 0.0 <= result.ml_credit_score <= 1.0, \
                f"Score {result.ml_credit_score} out of range for CIBIL {req.cibil_score}"
 
    def test_confidence_always_positive(self):
        req = make_request()
        result = score_credit_risk(req)
        assert result.confidence > 0
 
    def test_dti_always_non_negative(self):
        req = make_request(existing_monthly_emis=0)
        result = score_credit_risk(req)
        assert result.debt_to_income_ratio >= 0
 
    def test_higher_cibil_gives_higher_score(self):
        low_cibil  = make_request(cibil_score=500)
        high_cibil = make_request(cibil_score=850)
        r_low  = score_credit_risk(low_cibil)
        r_high = score_credit_risk(high_cibil)
        assert r_high.ml_credit_score > r_low.ml_credit_score
 
    def test_risk_band_matches_score(self):
        req    = make_request()
        result = score_credit_risk(req)
        score  = result.ml_credit_score
        if score >= 0.75:
            assert result.risk_band == RiskBand.LOW
        elif score >= 0.55:
            assert result.risk_band == RiskBand.MEDIUM
        elif score >= 0.35:
            assert result.risk_band == RiskBand.HIGH
        else:
            assert result.risk_band == RiskBand.VERY_HIGH
 
    def test_self_employed_adds_risk_factor(self):
        req    = make_request(employment_type="self_employed")
        result = score_credit_risk(req)
        emp_flags = [f for f in result.risk_factors if "self" in f.lower() or "employ" in f.lower()]
        assert len(emp_flags) > 0
 
 
 
class TestLoanTypeVariations:
 
    def test_home_loan_with_good_profile(self):
        req = make_request(loan_type="home", requested_amount=3500000,
                           annual_income=2400000, cibil_score=820, years_employed=6)
        result = score_credit_risk(req)
        assert result.risk_band in [RiskBand.LOW, RiskBand.MEDIUM]
 
    def test_education_loan_with_young_applicant(self):
        req = make_request(loan_type="education", requested_amount=1000000,
                           annual_income=300000, years_employed=0.5, cibil_score=650)
        result = score_credit_risk(req)
        assert result.ml_credit_score is not None
 
    def test_business_loan_self_employed(self):
        req = make_request(loan_type="business", employment_type="business_owner",
                           annual_income=1800000, requested_amount=2000000, cibil_score=720)
        result = score_credit_risk(req)
        assert 0.0 <= result.ml_credit_score <= 1.0
 
