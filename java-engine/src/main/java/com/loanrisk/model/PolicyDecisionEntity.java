package com.loanrisk.model;

import jakarta.persistence.*;
import java.time.Instant;


@Entity
@Table(name = "policy_decisions",
       indexes = {
           @Index(name = "idx_pd_application_id", columnList = "application_id"),
           @Index(name = "idx_pd_decision",       columnList = "decision"),
           @Index(name = "idx_pd_created_at",     columnList = "created_at")
       })
public class PolicyDecisionEntity {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "application_id", nullable = false)
    private Integer applicationId;

    @Column(name = "decision", nullable = false, length = 20)
    private String decision;          

    @Column(name = "loan_type", length = 20)
    private String loanType;

    @Column(name = "requested_amount", precision = 15)
    private Double requestedAmount;

    @Column(name = "approved_amount", precision = 15)
    private Double approvedAmount;

    @Column(name = "interest_rate")
    private Double interestRate;

    @Column(name = "monthly_emi")
    private Double monthlyEmi;

    @Column(name = "risk_band", length = 20)
    private String riskBand;

    @Column(name = "ml_credit_score")
    private Double mlCreditScore;

    @Column(name = "fraud_probability")
    private Double fraudProbability;

    @Column(name = "rejection_reason", columnDefinition = "TEXT")
    private String rejectionReason;

    @Column(name = "decision_notes", columnDefinition = "TEXT")
    private String decisionNotes;

    @Column(name = "created_at", nullable = false)
    private Instant createdAt;

    @PrePersist
    protected void onCreate() {
        this.createdAt = Instant.now();
    }

   
    public Long getId()                         { return id; }
    public Integer getApplicationId()           { return applicationId; }
    public void setApplicationId(Integer v)     { this.applicationId = v; }
    public String getDecision()                 { return decision; }
    public void setDecision(String v)           { this.decision = v; }
    public String getLoanType()                 { return loanType; }
    public void setLoanType(String v)           { this.loanType = v; }
    public Double getRequestedAmount()          { return requestedAmount; }
    public void setRequestedAmount(Double v)    { this.requestedAmount = v; }
    public Double getApprovedAmount()           { return approvedAmount; }
    public void setApprovedAmount(Double v)     { this.approvedAmount = v; }
    public Double getInterestRate()             { return interestRate; }
    public void setInterestRate(Double v)       { this.interestRate = v; }
    public Double getMonthlyEmi()               { return monthlyEmi; }
    public void setMonthlyEmi(Double v)         { this.monthlyEmi = v; }
    public String getRiskBand()                 { return riskBand; }
    public void setRiskBand(String v)           { this.riskBand = v; }
    public Double getMlCreditScore()            { return mlCreditScore; }
    public void setMlCreditScore(Double v)      { this.mlCreditScore = v; }
    public Double getFraudProbability()         { return fraudProbability; }
    public void setFraudProbability(Double v)   { this.fraudProbability = v; }
    public String getRejectionReason()          { return rejectionReason; }
    public void setRejectionReason(String v)    { this.rejectionReason = v; }
    public String getDecisionNotes()            { return decisionNotes; }
    public void setDecisionNotes(String v)      { this.decisionNotes = v; }
    public Instant getCreatedAt()               { return createdAt; }
}
