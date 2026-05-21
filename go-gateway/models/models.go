package models

import (
	"github.com/lib/pq"
	"time"
)

type LoanType string
type EmploymentType string
type ApplicationStatus string
type RiskBand string

const (
	LoanPersonal  LoanType = "personal"
	LoanHome      LoanType = "home"
	LoanVehicle   LoanType = "vehicle"
	LoanBusiness  LoanType = "business"
	LoanEducation LoanType = "education"

	EmployedSalaried EmploymentType = "salaried"
	EmployedSelf     EmploymentType = "self_employed"
	EmployedBusiness EmploymentType = "business_owner"

	StatusPending     ApplicationStatus = "pending"
	StatusUnderReview ApplicationStatus = "under_review"
	StatusApproved    ApplicationStatus = "approved"
	StatusRejected    ApplicationStatus = "rejected"
	StatusDisbursed   ApplicationStatus = "disbursed"

	RiskLow      RiskBand = "LOW"
	RiskMedium   RiskBand = "MEDIUM"
	RiskHigh     RiskBand = "HIGH"
	RiskVeryHigh RiskBand = "VERY_HIGH"
)

type LoanApplication struct {
	ID              int      `json:"id"`
	ApplicantName   string   `json:"applicant_name"`
	ApplicantEmail  string   `json:"applicant_email"`
	ApplicantPhone  string   `json:"applicant_phone"`
	LoanType        LoanType `json:"loan_type"`
	RequestedAmount float64  `json:"requested_amount"`
	TenureMonths    int      `json:"tenure_months"`
	Purpose         string   `json:"purpose"`

	AnnualIncome   float64        `json:"annual_income"`
	MonthlyEMIs    float64        `json:"existing_monthly_emis"`
	EmploymentType EmploymentType `json:"employment_type"`
	EmployerName   string         `json:"employer_name"`
	YearsEmployed  float64        `json:"years_employed"`
	CibilScore     int            `json:"cibil_score"`

	MLCreditScore    float64        `json:"ml_credit_score"`
	RiskBand         RiskBand       `json:"risk_band"`
	FraudProbability float64        `json:"fraud_probability"`
	RiskFactors      pq.StringArray `json:"risk_factors" gorm:"type:text[]"`

	Status          ApplicationStatus `json:"status"`
	ApprovedAmount  float64           `json:"approved_amount"`
	InterestRate    float64           `json:"interest_rate_percent"`
	MonthlyEMI      float64           `json:"monthly_emi"`
	RejectionReason string            `json:"rejection_reason,omitempty"`
	DecisionNotes   string            `json:"decision_notes,omitempty"`

	SubmittedBy string    `json:"submitted_by"`
	CreatedAt   time.Time `json:"created_at"`
	UpdatedAt   time.Time `json:"updated_at"`
}

type SubmitApplicationRequest struct {
	ApplicantName   string  `json:"applicant_name"    binding:"required,min=2"`
	ApplicantEmail  string  `json:"applicant_email"   binding:"required,email"`
	ApplicantPhone  string  `json:"applicant_phone"   binding:"required"`
	LoanType        string  `json:"loan_type"         binding:"required,oneof=personal home vehicle business education"`
	RequestedAmount float64 `json:"requested_amount"  binding:"required,min=10000"`
	TenureMonths    int     `json:"tenure_months"     binding:"required,min=6,max=360"`
	Purpose         string  `json:"purpose"           binding:"required,min=10"`
	AnnualIncome    float64 `json:"annual_income"     binding:"required,min=100000"`
	MonthlyEMIs     float64 `json:"existing_monthly_emis" binding:"min=0"`
	EmploymentType  string  `json:"employment_type"   binding:"required,oneof=salaried self_employed business_owner"`
	EmployerName    string  `json:"employer_name"     binding:"required"`
	YearsEmployed   float64 `json:"years_employed"    binding:"min=0"`
	CibilScore      int     `json:"cibil_score"       binding:"required,min=300,max=900"`
}

type UpdateStatusRequest struct {
	Status ApplicationStatus `json:"status" binding:"required,oneof=pending under_review approved rejected disbursed"`
	Notes  string            `json:"notes"`
}

type CreditScoreRequest struct {
	ApplicationID   int     `json:"application_id"`
	AnnualIncome    float64 `json:"annual_income"`
	MonthlyEMIs     float64 `json:"existing_monthly_emis"`
	EmploymentType  string  `json:"employment_type"`
	YearsEmployed   float64 `json:"years_employed"`
	CibilScore      int     `json:"cibil_score"`
	RequestedAmount float64 `json:"requested_amount"`
	LoanType        string  `json:"loan_type"`
}

type CreditScoreResponse struct {
	ApplicationID int      `json:"application_id"`
	MLScore       float64  `json:"ml_credit_score"`
	RiskBand      RiskBand `json:"risk_band"`
	RiskFactors   []string `json:"risk_factors"`
	DebtToIncome  float64  `json:"debt_to_income_ratio"`
	Confidence    float64  `json:"confidence"`
}

type FraudCheckRequest struct {
	ApplicationID   int     `json:"application_id"`
	ApplicantEmail  string  `json:"applicant_email"`
	ApplicantPhone  string  `json:"applicant_phone"`
	AnnualIncome    float64 `json:"annual_income"`
	RequestedAmount float64 `json:"requested_amount"`
	EmployerName    string  `json:"employer_name"`
}

type FraudCheckResponse struct {
	ApplicationID    int      `json:"application_id"`
	FraudProbability float64  `json:"fraud_probability"`
	IsSuspicious     bool     `json:"is_suspicious"`
	Flags            []string `json:"flags"`
}

type PolicyEvalRequest struct {
	ApplicationID    int      `json:"application_id"`
	LoanType         string   `json:"loan_type"`
	RequestedAmount  float64  `json:"requested_amount"`
	TenureMonths     int      `json:"tenure_months"`
	AnnualIncome     float64  `json:"annual_income"`
	MonthlyEMIs      float64  `json:"existing_monthly_emis"`
	CibilScore       int      `json:"cibil_score"`
	MLCreditScore    float64  `json:"ml_credit_score"`
	RiskBand         RiskBand `json:"risk_band"`
	FraudProbability float64  `json:"fraud_probability"`
	EmploymentType   string   `json:"employment_type"`
	YearsEmployed    float64  `json:"years_employed"`
}

type PolicyEvalResponse struct {
	ApplicationID   int     `json:"application_id"`
	Decision        string  `json:"decision"`
	ApprovedAmount  float64 `json:"approved_amount"`
	InterestRate    float64 `json:"interest_rate_percent"`
	MonthlyEMI      float64 `json:"monthly_emi"`
	RejectionReason string  `json:"rejection_reason,omitempty"`
	DecisionNotes   string  `json:"decision_notes"`
}

type EMIRequest struct {
	Principal    float64 `json:"principal"`
	AnnualRate   float64 `json:"annual_rate_percent"`
	TenureMonths int     `json:"tenure_months"`
}

type EMIResponse struct {
	MonthlyEMI    float64 `json:"monthly_emi"`
	TotalPayable  float64 `json:"total_payable"`
	TotalInterest float64 `json:"total_interest"`
}

type PipelineSummary struct {
	CreditScore      float64           `json:"credit_score"`
	RiskBand         RiskBand          `json:"risk_band"`
	DebtToIncome     float64           `json:"debt_to_income"`
	FraudProbability float64           `json:"fraud_probability"`
	IsSuspicious     bool              `json:"is_suspicious"`
	Decision         ApplicationStatus `json:"decision"`
}
