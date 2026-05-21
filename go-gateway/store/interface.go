package store

import "loan-risk/models"

type Storer interface {
	Save(app *models.LoanApplication)
	Update(app *models.LoanApplication)
	Get(id int) (*models.LoanApplication, bool)
	List(status string) []*models.LoanApplication
	UpdateStatus(id int, status models.ApplicationStatus, notes string) (*models.LoanApplication, bool)
	Stats() map[string]any
}
