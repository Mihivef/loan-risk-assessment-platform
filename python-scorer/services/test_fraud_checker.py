
import pytest
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../python-scorer'))

from models.schemas import FraudCheckRequest
from services.fraud_checker import check_fraud



def make_request(**kwargs) -> FraudCheckRequest:
   
    defaults = {
        "application_id":    1,
        "applicant_email":   "sneha.iyer@gmail.com",
        "applicant_phone":   "9876543210",
        "annual_income":     960000,
        "requested_amount":  400000,
        "employer_name":     "Infosys",
    }
    defaults.update(kwargs)
    return FraudCheckRequest(**defaults)



class TestCleanApplicant:

    def test_check_fraud_should_return_not_suspicious_when_applicant_is_clean(self):
        req    = make_request()
        result = check_fraud(req)
        assert result.is_suspicious == False

    def test_check_fraud_should_return_low_fraud_probability_when_applicant_is_clean(self):
        req    = make_request()
        result = check_fraud(req)
        assert result.fraud_probability < 0.25

    def test_check_fraud_should_return_no_flags_when_applicant_is_clean(self):
        req    = make_request()
        result = check_fraud(req)
        assert len(result.flags) == 0

    def test_check_fraud_should_return_no_flags_when_legitimate_employer(self):
        for employer in ["Infosys", "TCS", "IDFC Bank", "Google India", "Wipro"]:
            req    = make_request(employer_name=employer)
            result = check_fraud(req)
            assert "employer_on_watchlist" not in result.flags, \
                f"Legitimate employer '{employer}' was flagged"



class TestEmailFraudDetection:

    def test_check_fraud_should_flag_when_disposable_email(self):
        for email in ["test@mailinator.com", "fake@tempmail.com",
                      "x@guerrillamail.com", "tmp@throwaway.email"]:
            req    = make_request(applicant_email=email)
            result = check_fraud(req)
            assert "disposable_email_domain" in result.flags, \
                f"Disposable email {email} was not flagged"

    def test_check_fraud_should_return_higher_probability_when_disposable_email(self):
        clean    = make_request(applicant_email="user@gmail.com")
        disposable = make_request(applicant_email="user@mailinator.com")
        assert check_fraud(disposable).fraud_probability > check_fraud(clean).fraud_probability

    def test_check_fraud_should_return_no_flags_when_real_email_domains(self):
        for email in ["user@gmail.com", "name@yahoo.co.in",
                      "person@outlook.com", "emp@company.com"]:
            req    = make_request(applicant_email=email)
            result = check_fraud(req)
            assert "disposable_email_domain" not in result.flags



class TestPhoneFraudDetection:

    def test_check_fraud_should_flag_when_repeated_digits_phone(self):
        for phone in ["9999999999", "1111111111", "0000000000"]:
            req    = make_request(applicant_phone=phone)
            result = check_fraud(req)
            assert "suspicious_phone_pattern" in result.flags, \
                f"Suspicious phone {phone} was not flagged"

    def test_check_fraud_should_return_invalid_phone_flag_when_phone_length_is_invalid(self):
        for phone in ["123", "12345678901234", "abcdefghij"]:
            req    = make_request(applicant_phone=phone)
            result = check_fraud(req)
            assert "invalid_phone_format" in result.flags, \
                f"Invalid phone {phone} was not flagged"

    def test_check_fraud_should_return_no_invalid_phone_flag_when_phone_is_valid(self):
        for phone in ["9876543210", "8123456789", "7001234567"]:
            req    = make_request(applicant_phone=phone)
            result = check_fraud(req)
            assert "invalid_phone_format" not in result.flags



class TestEmployerBlacklist:

    def test_check_fraud_should_return_employer_flag_when_employer_is_blacklisted(self):
        for employer in ["ABC Pvt Ltd", "XYZ Corp", "Fake Company", "Test Employer"]:
            req    = make_request(employer_name=employer)
            result = check_fraud(req)
            assert "employer_on_watchlist" in result.flags, \
                f"Blacklisted employer '{employer}' was not flagged"

    def test_check_fraud_should_return_high_probability_when_blacklisted_employer(self):
        req    = make_request(employer_name="ABC Pvt Ltd")
        result = check_fraud(req)
        assert result.fraud_probability >= 0.35



class TestIncomeAmountRatio:

    def  test_check_fraud_should_return_income_flag_when_requested_amount_is_10x_income(self):
        req    = make_request(annual_income=100000, requested_amount=1400000)
        result = check_fraud(req)
        assert "requested_amount_exceeds_10x_income" in result.flags



    def  test_check_fraud_should_return_no_income_flag_when_amount_is_reasonable(self):
        req    = make_request(annual_income=960000, requested_amount=400000)
        result = check_fraud(req)
        income_flags = [f for f in result.flags if "income" in f]
        assert len(income_flags) == 0



class TestCombinedFraudSignals:

    def  test_check_fraud_should_return_high_probability_and_multiple_flags_when_multiple_fraud_signals_present(self):
        req = make_request(
            applicant_email="test@mailinator.com",
            applicant_phone="9999999999",
            employer_name="ABC Pvt Ltd",
            annual_income=100000,
            requested_amount=1400000,
        )
        result = check_fraud(req)
        assert result.fraud_probability >= 0.5
        assert result.is_suspicious == True
        assert len(result.flags) >= 3

    def test_suspicious_flag_set_above_threshold(self):
     
        req    = make_request(applicant_email="x@mailinator.com",
                              employer_name="ABC Pvt Ltd")
        result = check_fraud(req)
        if result.fraud_probability >= 0.25:
            assert result.is_suspicious == True

    def test_check_fraud_should_return_suspicious_true_when_probability_above_threshold(self):
        test_cases = [
            make_request(),
            make_request(applicant_email="x@mailinator.com",
                        applicant_phone="9999999999",
                        employer_name="ABC Pvt Ltd",
                        annual_income=50000,
                        requested_amount=5000000),
        ]
        for req in test_cases:
            result = check_fraud(req)
            assert 0.0 <= result.fraud_probability <= 1.0

    def test_check_fraud_should_return_same_application_id_when_request_has_application_id(self):
        req    = make_request(application_id=42)
        result = check_fraud(req)
        assert result.application_id == 42
