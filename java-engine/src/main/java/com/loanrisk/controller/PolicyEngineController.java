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
    public PolicyEngineController(PolicyEngineService service) {
        this.service = service;
    }

    @PostMapping("/evaluate")
    public ResponseEntity<PolicyEvalResponse> evaluate(@RequestBody PolicyEvalRequest req) {
        return ResponseEntity.ok(service.evaluate(req));
    }
      @PostMapping("/emi")
    public ResponseEntity<EmiResponse> calculateEmi(@RequestBody EmiRequest req) {
        return ResponseEntity.ok(service.calculateEmi(req));
    }
      @GetMapping("/policy/{loanType}")
    public ResponseEntity<?> getPolicy(@PathVariable String loanType) {
        return ResponseEntity.ok(service.getPolicy(loanType));
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
   

