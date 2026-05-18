package com.loanrisk.rules;

import com.loanrisk.model.PolicyEvalRequest;
import org.junit.jupiter.api.*;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.CsvSource;
import org.junit.jupiter.params.provider.ValueSource;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;


@DisplayName("Lending Policy Rules")
class LendingPolicyRulesTest {

    private LendingPolicyRules rules;

    @BeforeEach
    void setUp() {
        rules = new LendingPolicyRules();
    }

    private PolicyEvalRequest goodRequest() {
        PolicyEvalRequest r     = new PolicyEvalRequest();
        r.applicationId          = 1;
        r.loanType               = "personal";
        r.requestedAmount        = 400000;
        r.tenureMonths           = 36;
        r.annualIncome           = 960000;
        r.existingMonthlyEmis    = 3000;
        r.cibilScore             = 760;
        r.mlCreditScore          = 0.82;
        r.riskBand               = "LOW";
        r.fraudProbability       = 0.03;
        r.employmentType         = "salaried";
        r.yearsEmployed          = 3.5;
        return r;
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 1: Minimum CIBIL Score (650)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 1 — Minimum CIBIL Score (650)")
    class CibilRuleTest {

        @Test
        @DisplayName("CIBIL 760 passes")
        void cibil_760_passes() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = 760;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_CIBIL");
        }

        @Test
        @DisplayName("CIBIL exactly 650 passes (boundary)")
        void cibil_exactly_650_passes() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = 650;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_CIBIL");
        }

        @Test
        @DisplayName("CIBIL 649 fails (one below boundary)")
        void cibil_649_fails() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = 649;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_CIBIL");
        }

        @ParameterizedTest(name = "CIBIL {0} should fail MIN_CIBIL rule")
        @ValueSource(ints = {300, 400, 450, 500, 580, 620, 649})
        @DisplayName("All low CIBIL scores fail")
        void low_cibil_scores_fail(int cibil) {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = cibil;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_CIBIL");
        }

        @ParameterizedTest(name = "CIBIL {0} should pass MIN_CIBIL rule")
        @ValueSource(ints = {650, 700, 750, 800, 850, 900})
        @DisplayName("All valid CIBIL scores pass")
        void valid_cibil_scores_pass(int cibil) {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = cibil;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_CIBIL");
        }

        @Test
        @DisplayName("Violation message contains the actual CIBIL score")
        void violation_message_contains_cibil_value() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = 580;
            var violations = rules.evaluateHardRules(r);
            var minCibil = violations.stream()
                .filter(v -> v.rule().equals("MIN_CIBIL"))
                .findFirst()
                .orElseThrow();
            assertTrue(minCibil.reason().contains("580"),
                "Reason should mention the actual score: " + minCibil.reason());
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 2: Fraud Probability Threshold (25%)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 2 — Fraud Probability Threshold (25%)")
    class FraudRuleTest {

        @Test
        @DisplayName("Fraud 0.03 passes")
        void low_fraud_passes() {
            PolicyEvalRequest r = goodRequest();
            r.fraudProbability = 0.03;
            assertNoViolation(rules.evaluateHardRules(r), "FRAUD_THRESHOLD");
        }

        @Test
        @DisplayName("Fraud exactly 0.25 passes (boundary)")
        void fraud_at_threshold_passes() {
            PolicyEvalRequest r = goodRequest();
            r.fraudProbability = 0.25;
            assertNoViolation(rules.evaluateHardRules(r), "FRAUD_THRESHOLD");
        }

        @Test
        @DisplayName("Fraud 0.26 fails (one above boundary)")
        void fraud_above_threshold_fails() {
            PolicyEvalRequest r = goodRequest();
            r.fraudProbability = 0.26;
            assertHasViolation(rules.evaluateHardRules(r), "FRAUD_THRESHOLD");
        }

        @ParameterizedTest(name = "Fraud {0} should fail threshold rule")
        @ValueSource(doubles = {0.26, 0.30, 0.50, 0.75, 0.90, 1.00})
        @DisplayName("All high fraud probabilities fail")
        void high_fraud_fails(double fraud) {
            PolicyEvalRequest r = goodRequest();
            r.fraudProbability = fraud;
            assertHasViolation(rules.evaluateHardRules(r), "FRAUD_THRESHOLD");
        }

        @Test
        @DisplayName("Zero fraud probability passes")
        void zero_fraud_passes() {
            PolicyEvalRequest r = goodRequest();
            r.fraudProbability = 0.0;
            assertNoViolation(rules.evaluateHardRules(r), "FRAUD_THRESHOLD");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 3: Debt-to-Income Ratio (max 55%)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 3 — Debt-to-Income Ratio (max 55%)")
    class DTIRuleTest {

        @Test
        @DisplayName("Low existing EMIs passes DTI rule")
        void low_emis_passes() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 960000;  // monthly = 80,000
            r.existingMonthlyEmis = 3000;    // very low
            assertNoViolation(rules.evaluateHardRules(r), "MAX_DTI");
        }

        @Test
        @DisplayName("Very high existing EMIs fails DTI rule")
        void high_emis_fails() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 300000;  // monthly = 25,000
            r.existingMonthlyEmis = 18000;   // already 72% of income before new loan
            assertHasViolation(rules.evaluateHardRules(r), "MAX_DTI");
        }

        @Test
        @DisplayName("Zero existing EMIs passes DTI rule")
        void zero_emis_passes() {
            PolicyEvalRequest r = goodRequest();
            r.existingMonthlyEmis = 0;
            assertNoViolation(rules.evaluateHardRules(r), "MAX_DTI");
        }

        @Test
        @DisplayName("High income with high EMIs still passes DTI rule")
        void high_income_high_emis_passes() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 3600000; 
            r.existingMonthlyEmis = 50000;  
            assertNoViolation(rules.evaluateHardRules(r), "MAX_DTI");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 4: Minimum Employment Tenure (6 months = 0.5 years)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 4 — Minimum Employment Tenure (0.5 years)")
    class EmploymentTenureTest {

        @Test
        @DisplayName("3.5 years employment passes")
        void three_point_five_years_passes() {
            PolicyEvalRequest r = goodRequest();
            r.yearsEmployed = 3.5;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_EMPLOYMENT");
        }

        @Test
        @DisplayName("Exactly 0.5 years passes (boundary)")
        void half_year_passes() {
            PolicyEvalRequest r = goodRequest();
            r.yearsEmployed = 0.5;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_EMPLOYMENT");
        }

        @Test
        @DisplayName("0.3 years (3 months) fails")
        void three_months_fails() {
            PolicyEvalRequest r = goodRequest();
            r.yearsEmployed = 0.3;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_EMPLOYMENT");
        }

        @Test
        @DisplayName("0.0 years fails")
        void zero_years_fails() {
            PolicyEvalRequest r = goodRequest();
            r.yearsEmployed = 0.0;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_EMPLOYMENT");
        }

        @ParameterizedTest(name = "{0} years employment should pass")
        @ValueSource(doubles = {0.5, 1.0, 2.0, 5.0, 10.0, 20.0})
        @DisplayName("Valid employment tenures pass")
        void valid_tenures_pass(double years) {
            PolicyEvalRequest r = goodRequest();
            r.yearsEmployed = years;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_EMPLOYMENT");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 5: Minimum Annual Income (₹1.8 lakh)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 5 — Minimum Annual Income (₹1,80,000)")
    class MinIncomeTest {

        @Test
        @DisplayName("Income 960000 passes")
        void high_income_passes() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 960000;
            r.existingMonthlyEmis = 0;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_INCOME");
        }

        @Test
        @DisplayName("Income exactly 180000 passes (boundary)")
        void minimum_income_passes() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 180000;
            r.existingMonthlyEmis = 0;
            assertNoViolation(rules.evaluateHardRules(r), "MIN_INCOME");
        }

        @Test
        @DisplayName("Income 179999 fails (one below boundary)")
        void one_below_minimum_fails() {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = 179999;
            r.existingMonthlyEmis = 0;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_INCOME");
        }

        @ParameterizedTest(name = "Income ₹{0} should fail MIN_INCOME rule")
        @ValueSource(doubles = {50000, 100000, 150000, 179999})
        @DisplayName("Very low incomes fail")
        void low_incomes_fail(double income) {
            PolicyEvalRequest r = goodRequest();
            r.annualIncome        = income;
            r.existingMonthlyEmis = 0;
            assertHasViolation(rules.evaluateHardRules(r), "MIN_INCOME");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 6: Loan Amount Within Product Limits
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 6 — Loan Amount Within Product Limits")
    class LoanAmountLimitsTest {

        @ParameterizedTest(name = "{0} loan of ₹{1} should pass")
        @CsvSource({
            "personal,   10000",    // personal minimum
            "personal, 1500000",    // personal maximum
            "personal,  400000",    // typical personal
            "home,      500000",    // home minimum
            "home,    50000000",    // home maximum
            "home,    3500000",     // typical home
            "vehicle,    50000",    // vehicle minimum
            "vehicle,  5000000",    // vehicle maximum
            "business,  100000",    // business minimum
            "business, 10000000",   // business maximum
            "education,  50000",    // education minimum
            "education, 2500000",   // education maximum
        })
        @DisplayName("Valid amounts for each loan type pass")
        void valid_amounts_pass(String loanType, double amount) {
            PolicyEvalRequest r = goodRequest();
            r.loanType        = loanType;
            r.requestedAmount = amount;
            assertNoViolation(rules.evaluateHardRules(r), "LOAN_AMOUNT_LIMIT");
        }

        @ParameterizedTest(name = "{0} loan of ₹{1} should fail (out of range)")
        @CsvSource({
            "personal,      1000",   // below personal minimum
            "personal, 99000000",    // above personal maximum
            "home,       100000",    // below home minimum
            "home,    99000000",     // above home maximum
            "vehicle,     10000",    // below vehicle minimum
            "vehicle,  99000000",    // above vehicle maximum
        })
        @DisplayName("Out-of-range amounts fail")
        void invalid_amounts_fail(String loanType, double amount) {
            PolicyEvalRequest r = goodRequest();
            r.loanType        = loanType;
            r.requestedAmount = amount;
            assertHasViolation(rules.evaluateHardRules(r), "LOAN_AMOUNT_LIMIT");
        }

        @Test
        @DisplayName("Violation message shows the limits")
        void violation_message_shows_limits() {
            PolicyEvalRequest r = goodRequest();
            r.loanType        = "personal";
            r.requestedAmount = 9999; // below minimum
            var violations = rules.evaluateHardRules(r);
            var violation = violations.stream()
                .filter(v -> v.rule().equals("LOAN_AMOUNT_LIMIT"))
                .findFirst()
                .orElseThrow();
            assertNotNull(violation.reason());
            assertFalse(violation.reason().isEmpty());
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // RULE 7: VERY_HIGH Risk Band Auto-Reject
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Rule 7 — VERY_HIGH Risk Band Auto-Reject")
    class VeryHighRiskBandTest {

        @Test
        @DisplayName("VERY_HIGH risk band fails")
        void very_high_risk_fails() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand = "VERY_HIGH";
            assertHasViolation(rules.evaluateHardRules(r), "VERY_HIGH_RISK");
        }

        @ParameterizedTest(name = "Risk band {0} should NOT trigger VERY_HIGH rule")
        @ValueSource(strings = {"LOW", "MEDIUM", "HIGH"})
        @DisplayName("Non-VERY_HIGH bands don't trigger this rule")
        void non_very_high_bands_pass_this_rule(String band) {
            PolicyEvalRequest r = goodRequest();
            r.riskBand = band;
            assertNoViolation(rules.evaluateHardRules(r), "VERY_HIGH_RISK");
        }

        @Test
        @DisplayName("VERY_HIGH triggers rejection even with 900 CIBIL")
        void very_high_risk_overrides_good_cibil() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand   = "VERY_HIGH";
            r.cibilScore = 900;           // perfect CIBIL
            r.fraudProbability = 0.0;     // no fraud
            var violations = rules.evaluateHardRules(r);
            assertHasViolation(violations, "VERY_HIGH_RISK");
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Good applicant — all rules pass
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Good applicant — all 7 rules pass")
    class GoodApplicantTest {

        @Test
        @DisplayName("Perfect applicant has zero violations")
        void perfect_applicant_zero_violations() {
            var violations = rules.evaluateHardRules(goodRequest());
            assertEquals(0, violations.size(),
                "Expected 0 violations but got: " + violations);
        }

        @Test
        @DisplayName("Very bad applicant has multiple violations")
        void very_bad_applicant_multiple_violations() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore       = 300;     // fails Rule 1
            r.fraudProbability = 0.99;    // fails Rule 2
            r.annualIncome     = 50000;   // fails Rule 5
            r.yearsEmployed    = 0.0;     // fails Rule 4
            r.riskBand         = "VERY_HIGH"; // fails Rule 7
            var violations = rules.evaluateHardRules(r);
            assertTrue(violations.size() >= 4,
                "Expected at least 4 violations but got: " + violations.size());
        }

        @Test
        @DisplayName("Each violation has a non-empty rule code and reason")
        void violations_have_rule_and_reason() {
            PolicyEvalRequest r = goodRequest();
            r.cibilScore = 400;
            r.fraudProbability = 0.9;
            var violations = rules.evaluateHardRules(r);
            for (var v : violations) {
                assertNotNull(v.rule(), "Rule code should not be null");
                assertFalse(v.rule().isEmpty(), "Rule code should not be empty");
                assertNotNull(v.reason(), "Reason should not be null");
                assertFalse(v.reason().isEmpty(), "Reason should not be empty");
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Interest Rate Pricing
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Interest Rate Pricing by Risk Band")
    class InterestRatePricingTest {

        @Test
        @DisplayName("LOW risk gets 9.5%")
        void low_risk_rate_is_9_5() {
            assertEquals(9.5, rules.interestRateForRisk("LOW"), 0.001);
        }

        @Test
        @DisplayName("MEDIUM risk gets 11.5%")
        void medium_risk_rate_is_11_5() {
            assertEquals(11.5, rules.interestRateForRisk("MEDIUM"), 0.001);
        }

        @Test
        @DisplayName("HIGH risk gets 14.5%")
        void high_risk_rate_is_14_5() {
            assertEquals(14.5, rules.interestRateForRisk("HIGH"), 0.001);
        }

        @Test
        @DisplayName("VERY_HIGH risk gets 18.0%")
        void very_high_risk_rate_is_18() {
            assertEquals(18.0, rules.interestRateForRisk("VERY_HIGH"), 0.001);
        }

        @Test
        @DisplayName("Rates are strictly ordered LOW < MEDIUM < HIGH < VERY_HIGH")
        void rates_are_ordered() {
            double low      = rules.interestRateForRisk("LOW");
            double medium   = rules.interestRateForRisk("MEDIUM");
            double high     = rules.interestRateForRisk("HIGH");
            double veryHigh = rules.interestRateForRisk("VERY_HIGH");

            assertTrue(low < medium,   "LOW should be less than MEDIUM");
            assertTrue(medium < high,  "MEDIUM should be less than HIGH");
            assertTrue(high < veryHigh,"HIGH should be less than VERY_HIGH");
        }

        @Test
        @DisplayName("All rates are positive")
        void all_rates_are_positive() {
            for (String band : new String[]{"LOW","MEDIUM","HIGH","VERY_HIGH"}) {
                assertTrue(rules.interestRateForRisk(band) > 0,
                    band + " rate should be positive");
            }
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // EMI Calculation
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("EMI Calculation — Reducing Balance Formula")
    class EMICalculationTest {

        @Test
        @DisplayName("₹5,00,000 at 10.5% for 36 months ≈ ₹16,249")
        void standard_emi_5L_10_5pct_36months() {
            double emi = rules.calculateEmi(500000, 10.5, 36);
            assertEquals(16249.0, emi, 10.0); // ±₹10 tolerance for rounding
        }

        @Test
        @DisplayName("₹4,00,000 at 9.5% for 36 months ≈ ₹12,813")
        void emi_4L_9_5pct_36months() {
            double emi = rules.calculateEmi(400000, 9.5, 36);
            assertEquals(12813.0, emi, 10.0);
        }

        @Test
        @DisplayName("EMI is always positive")
        void emi_always_positive() {
            assertTrue(rules.calculateEmi(100000, 12.0, 12) > 0);
            assertTrue(rules.calculateEmi(5000000, 8.5, 240) > 0);
        }

        @Test
        @DisplayName("Doubling the principal doubles the EMI")
        void doubling_principal_doubles_emi() {
            double emi1 = rules.calculateEmi(300000, 10.0, 36);
            double emi2 = rules.calculateEmi(600000, 10.0, 36);
            assertEquals(emi2, emi1 * 2, 1.0);
        }

        @Test
        @DisplayName("Longer tenure gives lower EMI")
        void longer_tenure_gives_lower_emi() {
            double shortTenure = rules.calculateEmi(500000, 10.5, 12);
            double longTenure  = rules.calculateEmi(500000, 10.5, 60);
            assertTrue(shortTenure > longTenure,
                "Short tenure EMI (" + shortTenure + ") should be > long tenure (" + longTenure + ")");
        }

        @Test
        @DisplayName("Higher interest rate gives higher EMI")
        void higher_rate_gives_higher_emi() {
            double lowRate  = rules.calculateEmi(400000, 9.5,  36);
            double highRate = rules.calculateEmi(400000, 14.5, 36);
            assertTrue(highRate > lowRate,
                "High rate EMI (" + highRate + ") should be > low rate (" + lowRate + ")");
        }

        @Test
        @DisplayName("Total payment (EMI × tenure) always exceeds principal")
        void total_payment_exceeds_principal() {
            double principal = 500000;
            int    months    = 36;
            double emi       = rules.calculateEmi(principal, 10.5, months);
            double total     = emi * months;
            assertTrue(total > principal,
                "Total (" + total + ") should exceed principal (" + principal + ")");
        }

        @Test
        @DisplayName("Zero interest rate divides principal evenly")
        void zero_rate_divides_evenly() {
            double emi = rules.calculateEmi(360000, 0, 36);
            assertEquals(10000.0, emi, 0.01); // 360000 / 36 = 10000
        }

        @ParameterizedTest(name = "₹{0} at {1}% for {2} months — EMI should be positive")
        @CsvSource({
            "100000,  9.0,  12",
            "500000, 10.5,  36",
            "2000000, 8.5, 120",
            "5000000, 8.0, 240",
            "300000, 18.0,  24",
        })
        @DisplayName("EMI is positive for various loan scenarios")
        void emi_positive_for_various_scenarios(double p, double rate, int tenure) {
            assertTrue(rules.calculateEmi(p, rate, tenure) > 0);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Adjusted Approved Amount (soft rules)
    // ─────────────────────────────────────────────────────────────────────────

    @Nested
    @DisplayName("Soft Rules — Adjusted Approved Amount")
    class AdjustedApprovedAmountTest {

        @Test
        @DisplayName("LOW risk gets full requested amount")
        void low_risk_gets_full_amount() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand      = "LOW";
            r.mlCreditScore = 0.82;
            double approved  = rules.adjustedApprovedAmount(r);
            assertEquals(r.requestedAmount, approved, 1.0);
        }

        @Test
        @DisplayName("MEDIUM risk with score below 0.65 gets 80% of requested")
        void medium_risk_low_score_gets_80_percent() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand      = "MEDIUM";
            r.mlCreditScore = 0.58; // below 0.65 threshold
            double approved  = rules.adjustedApprovedAmount(r);
            assertEquals(r.requestedAmount * 0.80, approved, 1.0);
        }

        @Test
        @DisplayName("MEDIUM risk with score above 0.65 gets full amount")
        void medium_risk_good_score_gets_full_amount() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand      = "MEDIUM";
            r.mlCreditScore = 0.70; // above 0.65 threshold
            double approved  = rules.adjustedApprovedAmount(r);
            assertEquals(r.requestedAmount, approved, 1.0);
        }

        @Test
        @DisplayName("Self-employed is capped at 60% of annual income")
        void self_employed_capped_at_60_pct_income() {
            PolicyEvalRequest r = goodRequest();
            r.employmentType  = "self_employed";
            r.annualIncome    = 500000;
            r.requestedAmount = 2000000; // way more than 60% of income
            double approved    = rules.adjustedApprovedAmount(r);
            assertTrue(approved <= r.annualIncome * 0.60,
                "Self-employed approved (" + approved + ") should be <= 60% of income (" + r.annualIncome * 0.6 + ")");
        }

        @Test
        @DisplayName("Approved amount is never negative")
        void approved_amount_never_negative() {
            PolicyEvalRequest r = goodRequest();
            r.riskBand      = "MEDIUM";
            r.mlCreditScore = 0.40;
            assertTrue(rules.adjustedApprovedAmount(r) >= 0);
        }
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Helpers
    // ─────────────────────────────────────────────────────────────────────────

    private void assertHasViolation(List<LendingPolicyRules.RuleViolation> violations, String ruleCode) {
        assertTrue(
            violations.stream().anyMatch(v -> v.rule().equals(ruleCode)),
            "Expected violation '" + ruleCode + "' but got: " + violations
        );
    }

    private void assertNoViolation(List<LendingPolicyRules.RuleViolation> violations, String ruleCode) {
        assertTrue(
            violations.stream().noneMatch(v -> v.rule().equals(ruleCode)),
            "Did not expect violation '" + ruleCode + "' but got: " + violations
        );
    }
}