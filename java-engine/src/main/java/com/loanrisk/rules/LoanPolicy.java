package com.loanrisk.rules;

import java.util.Map;


public class LoanPolicy {

    public static final int    MIN_CIBIL_SCORE       = 650;
    public static final double MAX_FRAUD_PROBABILITY = 0.25;
    public static final double MAX_DEBT_TO_INCOME    = 0.55;
    public static final double MIN_YEARS_EMPLOYED    = 0.5;
    public static final double MIN_ANNUAL_INCOME     = 180_000;

    public static final double MEDIUM_RISK_SCORE_CUTOFF      = 0.65;
    public static final double MEDIUM_RISK_AMOUNT_REDUCTION  = 0.80;
    public static final double SELF_EMPLOYED_INCOME_CAP      = 0.60;
    public static final double SELF_EMPLOYED_RATE_PREMIUM    = 0.50;
    public static final double LOYALTY_YEARS_THRESHOLD       = 5.0;
    public static final double LOYALTY_RATE_DISCOUNT         = 0.25;

    public static final Map<String, Double> INTEREST_RATES = Map.of(
        "LOW",       9.5,
        "MEDIUM",   11.5,
        "HIGH",     14.5,
        "VERY_HIGH",18.0
    );
    public static final double DEFAULT_INTEREST_RATE = 13.0;

    public record ProductLimits(
        double minAmount,
        double maxAmount,
        int    minTenureMonths,
        int    maxTenureMonths,
        int    minCibil,
        Map<String, String> displayRates   
    ) {}

    public static final Map<String, ProductLimits> PRODUCT_LIMITS = Map.of(
        "personal", new ProductLimits(
            10_000, 1_500_000, 6, 60, 650,
            Map.of("LOW","9.5%","MEDIUM","11.5%","HIGH","14.5%")
        ),
        "home", new ProductLimits(
            500_000, 50_000_000, 12, 360, 700,
            Map.of("LOW","8.5%","MEDIUM","9.5%","HIGH","11.5%")
        ),
        "vehicle", new ProductLimits(
            50_000, 5_000_000, 12, 84, 650,
            Map.of("LOW","8.75%","MEDIUM","10.5%","HIGH","13.0%")
        ),
        "business", new ProductLimits(
            100_000, 10_000_000, 12, 84, 650,
            Map.of("LOW","9.5%","MEDIUM","12.0%","HIGH","15.0%")
        ),
        "education", new ProductLimits(
            50_000, 2_500_000, 12, 120, 600,
            Map.of("LOW","8.0%","MEDIUM","10.0%","HIGH","13.0%")
        )
    );
}
