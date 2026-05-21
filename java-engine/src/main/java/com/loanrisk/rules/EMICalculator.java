package com.loanrisk.rules;

import org.springframework.stereotype.Component;


@Component
public class EMICalculator {

  
    public double calculate(double principal, double annualRatePercent, int months) {
        if (months <= 0) throw new IllegalArgumentException("Tenure must be > 0");
        double r = annualRatePercent / 12.0 / 100.0;
        if (r == 0) return round2(principal / months);
        double powered = Math.pow(1 + r, months);
        return round2(principal * r * powered / (powered - 1));
    }

    public double totalPayable(double emi, int months) {
        return round2(emi * months);
    }

    public double totalInterest(double emi, int months, double principal) {
        return round2(totalPayable(emi, months) - principal);
    }

    private double round2(double val) {
        return Math.round(val * 100.0) / 100.0;
    }
}
