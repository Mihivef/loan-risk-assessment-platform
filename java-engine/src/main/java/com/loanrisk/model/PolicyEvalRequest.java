package com.loanrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;


public class PolicyEvalRequest {

    @JsonProperty("application_id")     public int    applicationId;
    @JsonProperty("loan_type")          public String loanType;
    @JsonProperty("requested_amount")   public double requestedAmount;
    @JsonProperty("tenure_months")      public int    tenureMonths;
    @JsonProperty("annual_income")      public double annualIncome;
    @JsonProperty("existing_monthly_emis") public double existingMonthlyEmis;
    @JsonProperty("cibil_score")        public int    cibilScore;
    @JsonProperty("ml_credit_score")    public double mlCreditScore;   // 0.0–1.0 from Python
    @JsonProperty("risk_band")          public String riskBand;        // LOW/MEDIUM/HIGH/VERY_HIGH
    @JsonProperty("fraud_probability")  public double fraudProbability; // 0.0–1.0 from Python
    @JsonProperty("employment_type")    public String employmentType;
    @JsonProperty("years_employed")     public double yearsEmployed;
}
