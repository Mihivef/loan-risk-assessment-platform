package com.loanrisk.rules;

import com.loanrisk.model.PolicyEvalRequest;
import org.springframework.stereotype.Component;


@Component
public class RateCalculator {

   
    public double calculateRate(PolicyEvalRequest req) {
        double rate = LoanPolicy.INTEREST_RATES
            .getOrDefault(req.riskBand, LoanPolicy.DEFAULT_INTEREST_RATE);

        if ("self_employed".equals(req.employmentType)) {
            rate += LoanPolicy.SELF_EMPLOYED_RATE_PREMIUM;
        }

        if (req.yearsEmployed >= LoanPolicy.LOYALTY_YEARS_THRESHOLD) {
            rate -= LoanPolicy.LOYALTY_RATE_DISCOUNT;
        }

        return round2(rate);
    }

  
    public double adjustedAmount(PolicyEvalRequest req) {
        double approved = req.requestedAmount;

        if ("MEDIUM".equals(req.riskBand)
                && req.mlCreditScore < LoanPolicy.MEDIUM_RISK_SCORE_CUTOFF) {
            approved *= LoanPolicy.MEDIUM_RISK_AMOUNT_REDUCTION;
        }

        if ("self_employed".equals(req.employmentType)) {
            approved = Math.min(approved,
                req.annualIncome * LoanPolicy.SELF_EMPLOYED_INCOME_CAP);
        }

        return round2(approved);
    }

    private double round2(double val) {
        return Math.round(val * 100.0) / 100.0;
    }
}
