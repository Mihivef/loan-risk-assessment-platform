package com.loanrisk.controller;

import com.loanrisk.model.*;
import com.loanrisk.rules.LendingPolicyRules;
import com.loanrisk.service.PolicyEngineService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

@RestController
@RequestMapping("/engine")
public class PolicyEngineController {

    private final PolicyEngineService service;
    private final LendingPolicyRules  rules;

    public PolicyEngineController(PolicyEngineService service, LendingPolicyRules rules) {
        this.service = service;
        this.rules   = rules;
    }


    @PostMapping("/evaluate")
    public ResponseEntity<PolicyEvalResponse> evaluate(@RequestBody PolicyEvalRequest req) {
        PolicyEvalResponse response = service.evaluate(req);
        int httpStatus = "APPROVED".equals(response.decision) ? 200 : 200; 
        return ResponseEntity.ok(response);
    }


    @PostMapping("/emi")
    public ResponseEntity<EmiResponse> calculateEmi(@RequestBody EmiRequest req) {
        return ResponseEntity.ok(service.calculateEmi(req));
    }


    @GetMapping("/policy/{loanType}")
    public ResponseEntity<?> getPolicy(@PathVariable String loanType) {
        Map<String, Object> policy = switch (loanType.toLowerCase()) {
            case "personal"  -> Map.of(
                "loan_type", "personal",
                "min_amount", 10_000, "max_amount", 1_500_000,
                "min_tenure_months", 6, "max_tenure_months", 60,
                "min_cibil", 650,
                "interest_rates", Map.of("LOW", "9.5%", "MEDIUM", "11.5%", "HIGH", "14.5%")
            );
            case "home"      -> Map.of(
                "loan_type", "home",
                "min_amount", 500_000, "max_amount", 50_000_000,
                "min_tenure_months", 12, "max_tenure_months", 360,
                "min_cibil", 700,
                "interest_rates", Map.of("LOW", "8.5%", "MEDIUM", "9.5%", "HIGH", "11.5%")
            );
            case "vehicle"   -> Map.of(
                "loan_type", "vehicle",
                "min_amount", 50_000, "max_amount", 5_000_000,
                "min_tenure_months", 12, "max_tenure_months", 84,
                "min_cibil", 650,
                "interest_rates", Map.of("LOW", "8.75%", "MEDIUM", "10.5%", "HIGH", "13.0%")
            );
            default -> Map.of("error", "unknown loan type: " + loanType);
        };
        return ResponseEntity.ok(policy);
    }

 
    @GetMapping("/health")
    public ResponseEntity<?> health() {
        return ResponseEntity.ok(Map.of(
            "status",    "ok",
            "service",   "java-policy-engine",
            "port",      8081,
            "endpoints", new String[]{
                "POST /engine/evaluate",
                "POST /engine/emi",
                "GET  /engine/policy/{loanType}"
            }
        ));
    }
}
