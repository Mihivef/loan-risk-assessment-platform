package com.loanrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;


public class PolicyEvalResponse {

    @JsonProperty("application_id")   public int    applicationId;
    @JsonProperty("decision")         public String decision;         // "APPROVED" or "REJECTED"
    @JsonProperty("approved_amount")  public double approvedAmount;
    @JsonProperty("interest_rate_percent") public double interestRate;
    @JsonProperty("monthly_emi")      public double monthlyEmi;
    @JsonProperty("rejection_reason") public String rejectionReason;
    @JsonProperty("decision_notes")   public String decisionNotes;


    public static PolicyEvalResponse approved(
            int id, double amount, double rate, double emi, String notes) {
        PolicyEvalResponse r = new PolicyEvalResponse();
        r.applicationId  = id;
        r.decision        = "APPROVED";
        r.approvedAmount  = amount;
        r.interestRate    = rate;
        r.monthlyEmi      = emi;
        r.decisionNotes   = notes;
        return r;
    }

    public static PolicyEvalResponse rejected(int id, String reason) {
        PolicyEvalResponse r = new PolicyEvalResponse();
        r.applicationId  = id;
        r.decision        = "REJECTED";
        r.approvedAmount  = 0;
        r.interestRate    = 0;
        r.monthlyEmi      = 0;
        r.rejectionReason = reason;
        r.decisionNotes   = "Application did not meet IDFC lending policy requirements";
        return r;
    }
}
