package handlers_test

import (
	"bytes"
	"encoding/json"
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"loan-risk/handlers"
	"loan-risk/middleware"
	"loan-risk/mocks"
	"loan-risk/models"

	"github.com/gin-gonic/gin"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func init() {
	gin.SetMode(gin.TestMode)
}

func newRouter(svc *mocks.MockLoanServicer) *gin.Engine {
	r := gin.New()
	h := handlers.New(svc)

	r.Use(func(c *gin.Context) {
		c.Set("user", middleware.UserInfo{Username: "test-user"})
		c.Next()
	})

	r.POST("/applications", h.SubmitApplication)
	r.GET("/applications", h.ListApplications)
	r.GET("/applications/:id", h.GetApplication)
	r.PATCH("/applications/:id/status", h.UpdateStatus)
	r.GET("/dashboard/stats", h.GetDashboardStats)
	r.GET("/emi/calculate", h.CalculateEMI)
	r.GET("/health", handlers.HealthCheck)

	return r
}

func doRequest(r *gin.Engine, method, path string, body interface{}) *httptest.ResponseRecorder {
	var buf bytes.Buffer
	if body != nil {
		json.NewEncoder(&buf).Encode(body)
	}
	req := httptest.NewRequest(method, path, &buf)
	req.Header.Set("Content-Type", "application/json")
	w := httptest.NewRecorder()
	r.ServeHTTP(w, req)
	return w
}

func sampleApp() *models.LoanApplication {
	return &models.LoanApplication{
		ID:              1,
		ApplicantName:   "Arjun Sharma",
		ApplicantEmail:  "arjun@example.com",
		LoanType:        models.LoanPersonal,
		RequestedAmount: 500000,
		Status:          models.StatusApproved,
		RiskBand:        models.RiskLow,
		RiskFactors:     []string{},
		SubmittedBy:     "test-user",
		CreatedAt:       time.Now(),
		UpdatedAt:       time.Now(),
	}
}

func sampleSummary() *models.PipelineSummary {
	return &models.PipelineSummary{
		CreditScore:      0.77,
		RiskBand:         models.RiskLow,
		DebtToIncome:     0.05,
		FraudProbability: 0.01,
		IsSuspicious:     false,
		Decision:         models.StatusApproved,
	}
}

func validSubmitBody() map[string]interface{} {
	return map[string]interface{}{
		"applicant_name":        "Arjun Sharma",
		"applicant_email":       "arjun@example.com",
		"applicant_phone":       "9876543210",
		"loan_type":             "personal",
		"requested_amount":      500000,
		"tenure_months":         36,
		"purpose":               "Home renovation and repair",
		"annual_income":         1200000,
		"existing_monthly_emis": 5000,
		"employment_type":       "salaried",
		"employer_name":         "Infosys Ltd",
		"years_employed":        4,
		"cibil_score":           760,
	}
}

func Test_submit_application_should_return_when_request_is_valid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("SubmitApplication", mock.AnythingOfType("models.SubmitApplicationRequest"), "test-user").
		Return(sampleApp(), sampleSummary(), nil)

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", validSubmitBody())

	assert.Equal(t, http.StatusCreated, w.Code)

	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.Equal(t, "application processed", resp["message"])
	assert.NotNil(t, resp["application"])
	assert.NotNil(t, resp["pipeline"])
	svc.AssertExpectations(t)
}

func Test_submit_application_should_return_when_service_returns_error(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("SubmitApplication", mock.Anything, mock.Anything).
		Return(nil, nil, fmt.Errorf("db unavailable"))

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", validSubmitBody())

	assert.Equal(t, http.StatusInternalServerError, w.Code)
	svc.AssertExpectations(t)
}

func Test_submit_application_should_return_when_applicant_name_is_missing(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	body := validSubmitBody()
	delete(body, "applicant_name")

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_submit_application_should_return_when_email_is_invalid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	body := validSubmitBody()
	body["applicant_email"] = "not-an-email"

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_submit_application_should_return_when_loan_type_is_invalid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	body := validSubmitBody()
	body["loan_type"] = "crypto"

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_submit_application_should_return_when_requested_amount_is_below_minimum(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	body := validSubmitBody()
	body["requested_amount"] = 100

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_submit_application_should_return_when_cibil_score_is_out_of_range(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	body := validSubmitBody()
	body["cibil_score"] = 100

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_submit_application_should_return_when_body_is_empty(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	w := doRequest(newRouter(svc), http.MethodPost, "/applications", nil)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "SubmitApplication")
}

func Test_list_applications_should_return_when_no_filter(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("ListApplications", "").Return([]*models.LoanApplication{sampleApp(), sampleApp()})

	w := doRequest(newRouter(svc), http.MethodGet, "/applications", nil)

	assert.Equal(t, http.StatusOK, w.Code)

	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.Equal(t, float64(2), resp["total"])
	svc.AssertExpectations(t)
}

func Test_list_applications_should_return_when_status_filter_is_passed(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("ListApplications", "approved").Return([]*models.LoanApplication{sampleApp()})

	w := doRequest(newRouter(svc), http.MethodGet, "/applications?status=approved", nil)

	assert.Equal(t, http.StatusOK, w.Code)
	svc.AssertCalled(t, "ListApplications", "approved")
}

func Test_get_application_should_return_when_id_is_valid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("GetApplication", 1).Return(sampleApp(), true)

	w := doRequest(newRouter(svc), http.MethodGet, "/applications/1", nil)

	assert.Equal(t, http.StatusOK, w.Code)
	svc.AssertExpectations(t)
}

func Test_get_application_should_return_when_not_found(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("GetApplication", 999).Return(nil, false)

	w := doRequest(newRouter(svc), http.MethodGet, "/applications/999", nil)

	assert.Equal(t, http.StatusNotFound, w.Code)
}

func Test_get_application_should_return_when_id_is_non_numeric(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	w := doRequest(newRouter(svc), http.MethodGet, "/applications/abc", nil)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "GetApplication")
}

func Test_update_status_should_return_when_request_is_valid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	updated := sampleApp()
	updated.Status = models.StatusDisbursed
	svc.On("UpdateStatus", 1, models.StatusDisbursed, "funds sent").Return(updated, true)

	body := map[string]interface{}{"status": "disbursed", "notes": "funds sent"}
	w := doRequest(newRouter(svc), http.MethodPatch, "/applications/1/status", body)

	assert.Equal(t, http.StatusOK, w.Code)

	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.Equal(t, "status updated", resp["message"])
	svc.AssertExpectations(t)
}

func Test_update_status_should_return_when_application_not_found(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("UpdateStatus", 999, mock.Anything, mock.Anything).Return(nil, false)

	body := map[string]interface{}{"status": "approved", "notes": ""}
	w := doRequest(newRouter(svc), http.MethodPatch, "/applications/999/status", body)

	assert.Equal(t, http.StatusNotFound, w.Code)
}

func Test_update_status_should_return_when_status_is_invalid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	body := map[string]interface{}{"status": "flying"}
	w := doRequest(newRouter(svc), http.MethodPatch, "/applications/1/status", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "UpdateStatus")
}

func Test_update_status_should_return_when_id_is_non_numeric(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	body := map[string]interface{}{"status": "approved"}
	w := doRequest(newRouter(svc), http.MethodPatch, "/applications/xyz/status", body)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "UpdateStatus")
}

func Test_get_dashboard_stats_should_return_when_service_returns_stats(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("Stats").Return(map[string]any{"total_applications": 5})

	w := doRequest(newRouter(svc), http.MethodGet, "/dashboard/stats", nil)

	assert.Equal(t, http.StatusOK, w.Code)
	svc.AssertExpectations(t)
}

func Test_calculate_emi_should_return_when_params_are_valid(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	emiResult := &models.EMIResponse{
		MonthlyEMI:    23537.0,
		TotalPayable:  565888.0,
		TotalInterest: 65888.0,
	}
	svc.On("CalculateEMI", 500000.0, 12.0, 24).Return(emiResult, nil)

	w := doRequest(newRouter(svc), http.MethodGet, "/emi/calculate?principal=500000&rate=12&tenure_months=24", nil)

	assert.Equal(t, http.StatusOK, w.Code)

	var resp models.EMIResponse
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.Equal(t, 23537.0, resp.MonthlyEMI)
	svc.AssertExpectations(t)
}

func Test_calculate_emi_should_return_when_params_are_missing(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	w := doRequest(newRouter(svc), http.MethodGet, "/emi/calculate?principal=500000", nil)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "CalculateEMI")
}

func Test_calculate_emi_should_return_when_principal_is_zero(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	w := doRequest(newRouter(svc), http.MethodGet, "/emi/calculate?principal=0&rate=12&tenure_months=24", nil)

	assert.Equal(t, http.StatusBadRequest, w.Code)
	svc.AssertNotCalled(t, "CalculateEMI")
}

func Test_calculate_emi_should_return_when_service_returns_error(t *testing.T) {
	svc := &mocks.MockLoanServicer{}
	svc.On("CalculateEMI", mock.Anything, mock.Anything, mock.Anything).
		Return(nil, fmt.Errorf("emi service down"))

	w := doRequest(newRouter(svc), http.MethodGet, "/emi/calculate?principal=500000&rate=12&tenure_months=24", nil)

	assert.Equal(t, http.StatusInternalServerError, w.Code)
}

func Test_health_check_should_return_when_called(t *testing.T) {
	svc := &mocks.MockLoanServicer{}

	w := doRequest(newRouter(svc), http.MethodGet, "/health", nil)

	assert.Equal(t, http.StatusOK, w.Code)

	var resp map[string]interface{}
	require.NoError(t, json.Unmarshal(w.Body.Bytes(), &resp))
	assert.Equal(t, "ok", resp["status"])
}
