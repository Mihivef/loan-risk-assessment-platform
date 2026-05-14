package store

import (
	"time"

	"loan-risk/db"
	"loan-risk/models"
)

type Store struct{}

func New() *Store {
	return &Store{}
}

func (s *Store) Save(app *models.LoanApplication) {

	db.DB.Create(app)
}

func (s *Store) Get(id int) (*models.LoanApplication, bool) {

	var app models.LoanApplication

	result := db.DB.First(&app, id)

	if result.Error != nil {
		return nil, false
	}

	return &app, true
}

func (s *Store) List(statusFilter string) []*models.LoanApplication {

	var apps []*models.LoanApplication

	query := db.DB

	if statusFilter != "" {
		query = query.Where("status = ?", statusFilter)
	}

	query.Find(&apps)

	return apps
}

func (s *Store) UpdateStatus(
	id int,
	status models.ApplicationStatus,
	notes string,
) (*models.LoanApplication, bool) {

	var app models.LoanApplication

	result := db.DB.First(&app, id)

	if result.Error != nil {
		return nil, false
	}

	app.Status = status

	if notes != "" {
		app.DecisionNotes = notes
	}

	app.UpdatedAt = time.Now()

	db.DB.Save(&app)

	return &app, true
}
func (s *Store) Update(app *models.LoanApplication) {

	db.DB.Save(app)
}
func (s *Store) Stats() map[string]any {

	var apps []models.LoanApplication

	db.DB.Find(&apps)

	total := len(apps)

	byStatus := make(map[string]int)
	byRisk := make(map[string]int)

	totalRequested := 0.0
	totalApproved := 0.0

	for _, a := range apps {

		byStatus[string(a.Status)]++
		byRisk[string(a.RiskBand)]++

		totalRequested += a.RequestedAmount
		totalApproved += a.ApprovedAmount
	}

	return map[string]any{
		"total_applications": total,
		"by_status":          byStatus,
		"by_risk_band":       byRisk,
		"total_requested":    totalRequested,
		"total_approved":     totalApproved,
	}

}
