package com.loanrisk.rules;

import com.loanrisk.model.PolicyEvalRequest;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;


@Component
public class LendingPolicyRules {


    private static final int    MIN_CIBIL_SCORE          = 650;
    private static final double MAX_FRAUD_PROBABILITY    = 0.25;
    private static final double MAX_DEBT_TO_INCOME       = 0.55;  // 55% of monthly income
    private static final double MIN_YEARS_EMPLOYED       = 0.5;
    private static final double MIN_ANNUAL_INCOME        = 180000; // ₹1.8 lakh

    private static final java.util.Map<String, double[]> LOAN_LIMITS = java.util.Map.of(
        "personal",  new double[]{10_000,   1_500_000},   // 10K – 15L
        "home",      new double[]{500_000,  50_000_000},  // 5L  – 5Cr
        "vehicle",   new double[]{50_000,   5_000_000},   // 50K – 50L
        "business",  new double[]{100_000,  10_000_000},  // 1L  – 1Cr
        "education", new double[]{50_000,   2_500_000}    // 50K – 25L
    );

  
    public record RuleViolation(String rule, String reason) {}

  
    public List<RuleViolation> evaluateHardRules(PolicyEvalRequest req) {
        List<RuleViolation> violations = new ArrayList<>();

        if (req.cibilScore < MIN_CIBIL_SCORE) {
            violations.add(new RuleViolation("MIN_CIBIL",
                String.format("CIBIL score %d is below minimum required %d", req.cibilScore, MIN_CIBIL_SCORE)));
        }

        if (req.fraudProbability > MAX_FRAUD_PROBABILITY) {
            violations.add(new RuleViolation("FRAUD_THRESHOLD",
                String.format("Fraud probability %.1f%% exceeds threshold %.1f%%",
                    req.fraudProbability * 100, MAX_FRAUD_PROBABILITY * 100)));
        }

        double monthlyIncome = req.annualIncome / 12.0;
        double estimatedEmi  = calculateEmi(req.requestedAmount, interestRateForRisk(req.riskBand), req.tenureMonths);
        double totalEmi      = req.existingMonthlyEmis + estimatedEmi;
        double dti           = monthlyIncome > 0 ? totalEmi / monthlyIncome : 1.0;

        if (dti > MAX_DEBT_TO_INCOME) {
            violations.add(new RuleViolation("MAX_DTI",
                String.format("Debt-to-income ratio %.1f%% exceeds policy limit %.1f%%",
                    dti * 100, MAX_DEBT_TO_INCOME * 100)));
        }

        if (req.yearsEmployed < MIN_YEARS_EMPLOYED) {
            violations.add(new RuleViolation("MIN_EMPLOYMENT",
                String.format("Employment tenure %.1f years is below minimum %.1f years",
                    req.yearsEmployed, MIN_YEARS_EMPLOYED)));
        }

        if (req.annualIncome < MIN_ANNUAL_INCOME) {
            violations.add(new RuleViolation("MIN_INCOME",
                String.format("Annual income ₹%.0f is below minimum ₹%.0f",
                    req.annualIncome, MIN_ANNUAL_INCOME)));
        }

        double[] limits = LOAN_LIMITS.getOrDefault(req.loanType, new double[]{0, 0});
        if (req.requestedAmount < limits[0] || req.requestedAmount > limits[1]) {
            violations.add(new RuleViolation("LOAN_AMOUNT_LIMIT",
                String.format("Requested ₹%.0f is outside %s loan range [₹%.0f – ₹%.0f]",
                    req.requestedAmount, req.loanType, limits[0], limits[1])));
        }

        if ("VERY_HIGH".equals(req.riskBand)) {
            violations.add(new RuleViolation("VERY_HIGH_RISK",
                "ML risk band VERY_HIGH — application does not meet risk appetite"));
        }

        return violations;
    }

 
    public double interestRateForRisk(String riskBand) {
        return switch (riskBand == null ? "" : riskBand) {
            case "LOW"       -> 9.5;
            case "MEDIUM"    -> 11.5;
            case "HIGH"      -> 14.5;
            case "VERY_HIGH" -> 18.0;
            default          -> 13.0;
        };
    }

    public double adjustedApprovedAmount(PolicyEvalRequest req) {
        double approved = req.requestedAmount;

        if ("MEDIUM".equals(req.riskBand) && req.mlCreditScore < 0.65) {
            approved = approved * 0.80;
        }

        if ("self_employed".equals(req.employmentType)) {
            approved = Math.min(approved, req.annualIncome * 0.60);
        }

        return Math.round(approved * 100.0) / 100.0;
    }

    public double calculateEmi(double principal, double annualRatePercent, int months) {
        double r = annualRatePercent / 12 / 100;
        if (r == 0) return principal / months;
        double powered = Math.pow(1 + r, months);
        return Math.round((principal * r * powered / (powered - 1)) * 100.0) / 100.0;
    }
}
