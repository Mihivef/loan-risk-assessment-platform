package com.loanrisk.service;

import com.loanrisk.model.*;
import com.loanrisk.rules.EMICalculator;
import com.loanrisk.rules.LendingPolicyRules;
import com.loanrisk.rules.RateCalculator;

import org.springframework.stereotype.Service;
import java.util.Map;

import java.util.List;


@Service
public class PolicyEngineService {

    private final LendingPolicyRules       rules;
    private final RateCalculator           rateCalc;   
    private final EMICalculator            emiCalc;
    private final PolicyDecisionRepository repo;

    public PolicyEngineService(LendingPolicyRules rules, RateCalculator rateCalc, EMICalculator emiCalc, PolicyDecisionRepository repo) {
        this.rules = rules;
        this.rateCalc = rateCalc;
        this.emiCalc = emiCalc;
        this.repo = repo;

    }
    public PolicyEvalResponse evaluate(PolicyEvalRequest req) {
        var violations = rules.evaluateHardRules(req);
        PolicyEvalResponse response;

        if (!violations.isEmpty()) {
            response = PolicyEvalResponse.rejected(req.applicationId,
                violations.get(0).reason());
        } else {
            double rate     = rateCalc.calculateRate(req);     
            double approved = rateCalc.adjustedAmount(req);     
            double emi      = emiCalc.calculate(approved, rate, req.tenureMonths); 
            response = PolicyEvalResponse.approved(req.applicationId,
                approved, rate, emi, buildNotes(req, rate, approved));
        }

        saveDecision(req, response);
        return response;
    }

   public EmiResponse calculateEmi(EmiRequest req) {
        double emi = emiCalc.calculate(req.principal, req.annualRate, req.tenureMonths);
        EmiResponse r  = new EmiResponse();
        r.monthlyEmi   = emi;
        r.totalPayable  = emiCalc.totalPayable(emi, req.tenureMonths);
        r.totalInterest = emiCalc.totalInterest(emi, req.tenureMonths, req.principal);
        return r;
    }

    private void saveDecision(PolicyEvalRequest req, PolicyEvalResponse resp) {
        PolicyDecisionEntity e = new PolicyDecisionEntity();
        e.setApplicationId(req.applicationId);
        e.setDecision(resp.decision);
        e.setLoanType(req.loanType);
        e.setRequestedAmount(req.requestedAmount);
        e.setApprovedAmount(resp.approvedAmount);
        e.setInterestRate(resp.interestRate);
        e.setMonthlyEmi(resp.monthlyEmi);
        e.setRiskBand(req.riskBand);
        e.setMlCreditScore(req.mlCreditScore);
        e.setFraudProbability(req.fraudProbability);
        e.setRejectionReason(resp.rejectionReason);
        e.setDecisionNotes(resp.decisionNotes);
        repo.save(e);
    }

    private String buildNotes(PolicyEvalRequest req, double rate, double approved) {
        var sb = new StringBuilder();
        sb.append(String.format("Approved at %.2f%% p.a. (risk: %s). ", rate, req.riskBand));
        if (approved < req.requestedAmount)
            sb.append(String.format("Amount adjusted ₹%.0f→₹%.0f. ", req.requestedAmount, approved));
        if ("self_employed".equals(req.employmentType)) sb.append("+0.5% self-employment premium. ");
        if (req.yearsEmployed >= 5)                     sb.append("-0.25% loyalty discount. ");
        return sb.toString().trim();
    }
    public Map<String, Object> getPolicy(String loanType) {
        return rules.getPolicyForLoanType(loanType);
}
}
