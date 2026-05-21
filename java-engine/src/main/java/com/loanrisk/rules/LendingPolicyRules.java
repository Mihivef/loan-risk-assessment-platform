package com.loanrisk.rules;

import com.loanrisk.model.PolicyEvalRequest;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;


@Component
public class LendingPolicyRules {

    private final EMICalculator emiCalc;

    public LendingPolicyRules(EMICalculator emiCalc) {
        this.emiCalc = emiCalc;
    }

    public record RuleViolation(String rule, String reason) {}


    public List<RuleViolation> evaluateHardRules(PolicyEvalRequest req) {
        List<RuleViolation> violations = new ArrayList<>();

        checkCibil(req, violations);
        checkFraud(req, violations);
        checkDTI(req, violations);
        checkEmploymentTenure(req, violations);
        checkMinIncome(req, violations);
        checkLoanAmountLimits(req, violations);
        checkVeryHighRisk(req, violations);

        return violations;
    }


    private void checkCibil(PolicyEvalRequest req, List<RuleViolation> v) {
        if (req.cibilScore < LoanPolicy.MIN_CIBIL_SCORE) {
            v.add(new RuleViolation("MIN_CIBIL",
                String.format("CIBIL score %d is below minimum required %d",
                    req.cibilScore, LoanPolicy.MIN_CIBIL_SCORE)));
        }
    }


    private void checkFraud(PolicyEvalRequest req, List<RuleViolation> v) {
        if (req.fraudProbability > LoanPolicy.MAX_FRAUD_PROBABILITY) {
            v.add(new RuleViolation("FRAUD_THRESHOLD",
                String.format("Fraud probability %.1f%% exceeds threshold %.1f%%",
                    req.fraudProbability * 100, LoanPolicy.MAX_FRAUD_PROBABILITY * 100)));
        }
    }


    private void checkDTI(PolicyEvalRequest req, List<RuleViolation> v) {
        double monthlyIncome = req.annualIncome / 12.0;
        double estimatedEmi  = emiCalc.calculate(
            req.requestedAmount,
            LoanPolicy.INTEREST_RATES.getOrDefault(req.riskBand, LoanPolicy.DEFAULT_INTEREST_RATE),
            req.tenureMonths
        );
        double dti = monthlyIncome > 0
            ? (req.existingMonthlyEmis + estimatedEmi) / monthlyIncome
            : 1.0;

        if (dti > LoanPolicy.MAX_DEBT_TO_INCOME) {
            v.add(new RuleViolation("MAX_DTI",
                String.format("Debt-to-income ratio %.1f%% exceeds policy limit %.1f%%",
                    dti * 100, LoanPolicy.MAX_DEBT_TO_INCOME * 100)));
        }
    }


    private void checkEmploymentTenure(PolicyEvalRequest req, List<RuleViolation> v) {
        if (req.yearsEmployed < LoanPolicy.MIN_YEARS_EMPLOYED) {
            v.add(new RuleViolation("MIN_EMPLOYMENT",
                String.format("Employment tenure %.1f years is below minimum %.1f years",
                    req.yearsEmployed, LoanPolicy.MIN_YEARS_EMPLOYED)));
        }
    }


    private void checkMinIncome(PolicyEvalRequest req, List<RuleViolation> v) {
        if (req.annualIncome < LoanPolicy.MIN_ANNUAL_INCOME) {
            v.add(new RuleViolation("MIN_INCOME",
                String.format("Annual income ₹%.0f is below minimum ₹%.0f",
                    req.annualIncome, LoanPolicy.MIN_ANNUAL_INCOME)));
        }
    }


    private void checkLoanAmountLimits(PolicyEvalRequest req, List<RuleViolation> v) {
        var limits = LoanPolicy.PRODUCT_LIMITS.get(req.loanType);
        if (limits == null || req.requestedAmount < limits.minAmount()
                           || req.requestedAmount > limits.maxAmount()) {
            double min = limits != null ? limits.minAmount() : 0;
            double max = limits != null ? limits.maxAmount() : 0;
            v.add(new RuleViolation("LOAN_AMOUNT_LIMIT",
                String.format("Requested ₹%.0f is outside %s loan range [₹%.0f – ₹%.0f]",
                    req.requestedAmount, req.loanType, min, max)));
        }
    }


    private void checkVeryHighRisk(PolicyEvalRequest req, List<RuleViolation> v) {
        if ("VERY_HIGH".equals(req.riskBand)) {
            v.add(new RuleViolation("VERY_HIGH_RISK",
                "ML risk band VERY_HIGH — application does not meet risk appetite"));
        }
    }


    public Map<String, Object> getPolicyForLoanType(String loanType) {
        var limits = LoanPolicy.PRODUCT_LIMITS.get(loanType.toLowerCase());
        if (limits == null) return Map.of("error", "unknown loan type: " + loanType);

        return Map.of(
            "loan_type",          loanType,
            "min_amount",         limits.minAmount(),
            "max_amount",         limits.maxAmount(),
            "min_tenure_months",  limits.minTenureMonths(),
            "max_tenure_months",  limits.maxTenureMonths(),
            "min_cibil",          limits.minCibil(),
            "interest_rates",     limits.displayRates()
        );
    }
}
