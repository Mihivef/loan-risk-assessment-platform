package com.loanrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class EmiResponse {
    @JsonProperty("monthly_emi")    public double monthlyEmi;
    @JsonProperty("total_payable")  public double totalPayable;
    @JsonProperty("total_interest") public double totalInterest;
}
