package com.loanrisk.service;

import com.loanrisk.model.*;
import com.loanrisk.rules.LendingPolicyRules;
import org.springframework.stereotype.Service;

import java.util.List;


@Service
public class PolicyEngineService {

    private final LendingPolicyRules       rules;
    private final PolicyDecisionRepository repo;

    public PolicyEngineService(LendingPolicyRules rules, PolicyDecisionRepository repo) {
        this.rules = rules;
        this.repo  = repo;
    }

    public PolicyEvalResponse evaluate(PolicyEvalRequest req) {
        List<LendingPolicyRules.RuleViolation> violations = rules.evaluateHardRules(req);
        PolicyEvalResponse response;

        if (!violations.isEmpty()) {
            response = PolicyEvalResponse.rejected(req.applicationId, violations.get(0).reason());
        } else {
            double rate = rules.interestRateForRisk(req.riskBand);
            if ("self_employed".equals(req.employmentType)) rate += 0.5;
            if (req.yearsEmployed >= 5)                     rate -= 0.25;
            rate = Math.round(rate * 100.0) / 100.0;

            double approved = rules.adjustedApprovedAmount(req);
            double emi      = rules.calculateEmi(approved, rate, req.tenureMonths);
            response = PolicyEvalResponse.approved(req.applicationId, approved, rate, emi,
                buildNotes(req, rate, approved));
        }

        saveDecision(req, response);
        return response;
    }

    public EmiResponse calculateEmi(EmiRequest req) {
        double emi   = rules.calculateEmi(req.principal, req.annualRate, req.tenureMonths);
        double total = Math.round(emi * req.tenureMonths * 100.0) / 100.0;
        EmiResponse r = new EmiResponse();
        r.monthlyEmi    = emi;
        r.totalPayable  = total;
        r.totalInterest = Math.round((total - req.principal) * 100.0) / 100.0;
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
}
