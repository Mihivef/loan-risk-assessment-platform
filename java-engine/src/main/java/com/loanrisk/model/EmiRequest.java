package com.loanrisk.model;

import com.fasterxml.jackson.annotation.JsonProperty;

public class EmiRequest {
    @JsonProperty("principal")        public double principal;
    @JsonProperty("annual_rate_percent") public double annualRate;
    @JsonProperty("tenure_months")    public int    tenureMonths;
}
