package service

import "loan-risk/models"

type LoanServicer interface {
	SubmitApplication(req models.SubmitApplicationRequest, submittedBy string) (*models.LoanApplication, *models.PipelineSummary, error)
	GetApplication(id int) (*models.LoanApplication, bool)
	ListApplications(status string) []*models.LoanApplication
	UpdateStatus(id int, status models.ApplicationStatus, notes string) (*models.LoanApplication, bool)
	Stats() map[string]any
	CalculateEMI(principal, annualRate float64, tenureMonths int) (*models.EMIResponse, error)
}
