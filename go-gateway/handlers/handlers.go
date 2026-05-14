package handlers

import (
	"fmt"
	"math"
	"net/http"
	"strconv"
	"time"

	"loan-risk/clients"
	"loan-risk/middleware"
	"loan-risk/models"
	"loan-risk/store"

	"github.com/gin-gonic/gin"
)

type Handler struct {
	Store *store.Store
}

func New(s *store.Store) *Handler {
	return &Handler{Store: s}
}

func (h *Handler) SubmitApplication(c *gin.Context) {
	var req models.SubmitApplicationRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "validation failed",
			"details": err.Error(),
		})
		return
	}

	user, _ := c.Get("user")
	u := user.(middleware.UserInfo)

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
		SubmittedBy:     u.Username,
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}

	h.Store.Save(app)

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
		if policyResp.Decision == "APPROVED" {
			app.Status = models.StatusApproved
		} else {
			app.Status = models.StatusRejected
		}

		app.ApprovedAmount = policyResp.ApprovedAmount
		app.InterestRate = policyResp.InterestRate
		app.MonthlyEMI = policyResp.MonthlyEMI
		app.RejectionReason = policyResp.RejectionReason
		app.DecisionNotes = policyResp.DecisionNotes
	}

	app.UpdatedAt = time.Now()
	h.Store.Update(app)

	c.JSON(http.StatusCreated, gin.H{
		"message":     "application processed",
		"application": app,
		"pipeline": gin.H{
			"credit_score":      creditResp.MLScore,
			"risk_band":         creditResp.RiskBand,
			"debt_to_income":    creditResp.DebtToIncome,
			"fraud_probability": fraudResp.FraudProbability,
			"is_suspicious":     fraudResp.IsSuspicious,
			"decision":          app.Status,
		},
	})
}

func (h *Handler) ListApplications(c *gin.Context) {
	status := c.Query("status")
	apps := h.Store.List(status)

	c.JSON(http.StatusOK, gin.H{
		"total":        len(apps),
		"applications": apps,
	})
}

func (h *Handler) GetApplication(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id must be a number",
		})
		return
	}

	app, ok := h.Store.Get(id)

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("application %d not found", id),
		})
		return
	}

	c.JSON(http.StatusOK, app)
}

func (h *Handler) UpdateStatus(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))

	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id must be a number",
		})
		return
	}

	var req models.UpdateStatusRequest

	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error":   "validation failed",
			"details": err.Error(),
		})
		return
	}

	app, ok := h.Store.UpdateStatus(id, req.Status, req.Notes)

	if !ok {
		c.JSON(http.StatusNotFound, gin.H{
			"error": fmt.Sprintf("application %d not found", id),
		})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message":     "status updated",
		"application": app,
	})
}

func (h *Handler) GetDashboardStats(c *gin.Context) {
	c.JSON(http.StatusOK, h.Store.Stats())
}

func (h *Handler) CalculateEMI(c *gin.Context) {
	principal, _ := strconv.ParseFloat(c.Query("principal"), 64)
	rate, _ := strconv.ParseFloat(c.Query("rate"), 64)
	tenure, _ := strconv.Atoi(c.Query("tenure_months"))

	if principal <= 0 || rate <= 0 || tenure <= 0 {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "provide principal, rate, and tenure_months",
		})
		return
	}

	result, err := clients.CalculateEMI(models.EMIRequest{
		Principal:    principal,
		AnnualRate:   rate,
		TenureMonths: tenure,
	})

	if err != nil {
		result = localEMI(principal, rate, tenure)
	}

	c.JSON(http.StatusOK, result)
}

func HealthCheck(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "ok",
		"service": "go-gateway",
		"port":    8080,
	})
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
