package service

import (
	"math"
	"time"

	"loan-risk/clients"
	"loan-risk/models"
	"loan-risk/store"
)

type LoanService struct {
	Store store.Storer
}

func New(s store.Storer) *LoanService {
	return &LoanService{Store: s}
}

func (s *LoanService) SubmitApplication(req models.SubmitApplicationRequest, submittedBy string) (*models.LoanApplication, *models.PipelineSummary, error) {
	app := &models.LoanApplication{
		ApplicantName:   req.ApplicantName,
		ApplicantEmail:  req.ApplicantEmail,
		ApplicantPhone:  req.ApplicantPhone,
		LoanType:        models.LoanType(req.LoanType),
		RequestedAmount: req.RequestedAmount,
		TenureMonths:    req.TenureMonths,
		Purpose:         req.Purpose,
		AnnualIncome:    req.AnnualIncome,
		MonthlyEMIs:     req.MonthlyEMIs,
		EmploymentType:  models.EmploymentType(req.EmploymentType),
		EmployerName:    req.EmployerName,
		YearsEmployed:   req.YearsEmployed,
		CibilScore:      req.CibilScore,
		Status:          models.StatusPending,
		RiskFactors:     []string{},
		SubmittedBy:     submittedBy,
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	s.Store.Save(app)

	creditResp, err := clients.GetCreditScore(models.CreditScoreRequest{
		ApplicationID:   app.ID,
		AnnualIncome:    app.AnnualIncome,
		MonthlyEMIs:     app.MonthlyEMIs,
		EmploymentType:  string(app.EmploymentType),
		YearsEmployed:   app.YearsEmployed,
		CibilScore:      app.CibilScore,
		RequestedAmount: app.RequestedAmount,
		LoanType:        string(app.LoanType),
	})
	if err != nil {
		creditResp = fallbackCreditScore(app)
	}

	app.MLCreditScore = creditResp.MLScore
	app.RiskBand = creditResp.RiskBand
	app.RiskFactors = creditResp.RiskFactors

	fraudResp, err := clients.CheckFraud(models.FraudCheckRequest{
		ApplicationID:   app.ID,
		ApplicantEmail:  app.ApplicantEmail,
		ApplicantPhone:  app.ApplicantPhone,
		AnnualIncome:    app.AnnualIncome,
		RequestedAmount: app.RequestedAmount,
		EmployerName:    app.EmployerName,
	})
	if err != nil {
		fraudResp = &models.FraudCheckResponse{
			FraudProbability: 0,
			IsSuspicious:     false,
			Flags:            []string{},
		}
	}

	app.FraudProbability = fraudResp.FraudProbability

	if fraudResp.IsSuspicious {
		app.RiskFactors = append(app.RiskFactors, fraudResp.Flags...)
	}

	policyResp, err := clients.EvaluatePolicy(models.PolicyEvalRequest{
		ApplicationID:    app.ID,
		LoanType:         string(app.LoanType),
		RequestedAmount:  app.RequestedAmount,
		TenureMonths:     app.TenureMonths,
		AnnualIncome:     app.AnnualIncome,
		MonthlyEMIs:      app.MonthlyEMIs,
		CibilScore:       app.CibilScore,
		MLCreditScore:    app.MLCreditScore,
		RiskBand:         app.RiskBand,
		FraudProbability: app.FraudProbability,
		EmploymentType:   string(app.EmploymentType),
		YearsEmployed:    app.YearsEmployed,
	})
	if err != nil {
		app.Status = models.StatusUnderReview
		app.DecisionNotes = "Policy engine unavailable; manual review required"
	} else {
		applyPolicyDecision(app, policyResp)
	}

	app.UpdatedAt = time.Now()
	s.Store.Update(app)

	summary := &models.PipelineSummary{
		CreditScore:      creditResp.MLScore,
		RiskBand:         creditResp.RiskBand,
		DebtToIncome:     creditResp.DebtToIncome,
		FraudProbability: fraudResp.FraudProbability,
		IsSuspicious:     fraudResp.IsSuspicious,
		Decision:         app.Status,
	}

	return app, summary, nil
}

func (s *LoanService) GetApplication(id int) (*models.LoanApplication, bool) {
	return s.Store.Get(id)
}

func (s *LoanService) ListApplications(status string) []*models.LoanApplication {
	return s.Store.List(status)
}

func (s *LoanService) UpdateStatus(id int, status models.ApplicationStatus, notes string) (*models.LoanApplication, bool) {
	return s.Store.UpdateStatus(id, status, notes)
}

func (s *LoanService) Stats() map[string]any {
	return s.Store.Stats()
}

func (s *LoanService) CalculateEMI(principal, annualRate float64, tenureMonths int) (*models.EMIResponse, error) {
	result, err := clients.CalculateEMI(models.EMIRequest{
		Principal:    principal,
		AnnualRate:   annualRate,
		TenureMonths: tenureMonths,
	})
	if err != nil {
		return localEMI(principal, annualRate, tenureMonths), nil
	}
	return result, nil
}

func applyPolicyDecision(app *models.LoanApplication, resp *models.PolicyEvalResponse) {
	if resp.Decision == "APPROVED" {
		app.Status = models.StatusApproved
	} else {
		app.Status = models.StatusRejected
	}

	app.ApprovedAmount = resp.ApprovedAmount
	app.InterestRate = resp.InterestRate
	app.MonthlyEMI = resp.MonthlyEMI
	app.RejectionReason = resp.RejectionReason
	app.DecisionNotes = resp.DecisionNotes
}

func fallbackCreditScore(app *models.LoanApplication) *models.CreditScoreResponse {
	score := float64(app.CibilScore-300) / 600.0

	band := models.RiskHigh
	if app.CibilScore >= 750 {
		band = models.RiskLow
	} else if app.CibilScore >= 650 {
		band = models.RiskMedium
	}

	return &models.CreditScoreResponse{
		ApplicationID: app.ID,
		MLScore:       score,
		RiskBand:      band,
		RiskFactors:   []string{"scored_via_fallback"},
		DebtToIncome:  (app.MonthlyEMIs * 12) / app.AnnualIncome,
		Confidence:    0.5,
	}
}

func localEMI(principal, annualRate float64, months int) *models.EMIResponse {
	r := annualRate / 12 / 100
	pow := math.Pow(1+r, float64(months))
	emi := principal * r * pow / (pow - 1)
	total := emi * float64(months)

	return &models.EMIResponse{
		MonthlyEMI:    round2(emi),
		TotalPayable:  round2(total),
		TotalInterest: round2(total - principal),
	}
}

func round2(v float64) float64 {
	return float64(int(v*100+0.5)) / 100
}
