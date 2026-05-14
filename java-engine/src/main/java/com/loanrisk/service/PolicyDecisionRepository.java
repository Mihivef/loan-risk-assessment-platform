package com.loanrisk.service;

import com.loanrisk.model.PolicyDecisionEntity;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Map;


@Repository
public interface PolicyDecisionRepository extends JpaRepository<PolicyDecisionEntity, Long> {

    List<PolicyDecisionEntity> findByApplicationId(Integer applicationId);

    List<PolicyDecisionEntity> findByDecision(String decision);

    @Query("SELECT p.decision, COUNT(p) FROM PolicyDecisionEntity p GROUP BY p.decision")
    List<Object[]> countByDecision();

    @Query("SELECT AVG(p.approvedAmount) FROM PolicyDecisionEntity p WHERE p.decision = 'APPROVED'")
    Double avgApprovedAmount();
}
