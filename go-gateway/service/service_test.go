package service_test

import (
	"testing"

	"loan-risk/mocks"
	"loan-risk/models"
	"loan-risk/service"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/mock"
	"github.com/stretchr/testify/require"
)

func newSvc(mockStore *mocks.MockStorer) *service.LoanService {
	return service.New(mockStore)
}

func validRequest() models.SubmitApplicationRequest {
	return models.SubmitApplicationRequest{
		ApplicantName:   "Mihika Sharma",
		ApplicantEmail:  "arjun@example.com",
		ApplicantPhone:  "9876543210",
		LoanType:        "personal",
		RequestedAmount: 500000,
		TenureMonths:    36,
		Purpose:         "Home renovation and repair",
		AnnualIncome:    1200000,
		MonthlyEMIs:     5000,
		EmploymentType:  "salaried",
		EmployerName:    "Infosys Ltd",
		YearsEmployed:   4,
		CibilScore:      760,
	}
}

func setupSubmitMocks(ms *mocks.MockStorer) {
	ms.On("Save", mock.AnythingOfType("*models.LoanApplication")).
		Run(func(args mock.Arguments) {
			app := args.Get(0).(*models.LoanApplication)
			app.ID = 1
		}).Return()
	ms.On("Update", mock.AnythingOfType("*models.LoanApplication")).Return()
}

func Test_submit_application_should_return_low_risk_band_when_cibil_is_high(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	req := validRequest()
	req.CibilScore = 760

	app, summary, err := newSvc(ms).SubmitApplication(req, "test-user")

	require.NoError(t, err)
	assert.Equal(t, models.RiskLow, app.RiskBand)
	assert.Equal(t, models.RiskLow, summary.RiskBand)
	assert.Contains(t, app.RiskFactors, "scored_via_fallback")
	ms.AssertExpectations(t)
}

func Test_submit_application_should_return_medium_risk_band_when_cibil_is_mid(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	req := validRequest()
	req.CibilScore = 680

	app, _, err := newSvc(ms).SubmitApplication(req, "test-user")

	require.NoError(t, err)
	assert.Equal(t, models.RiskMedium, app.RiskBand)
	ms.AssertExpectations(t)
}

func Test_submit_application_should_return_high_risk_band_when_cibil_is_low(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	req := validRequest()
	req.CibilScore = 580

	app, _, err := newSvc(ms).SubmitApplication(req, "test-user")

	require.NoError(t, err)
	assert.Equal(t, models.RiskHigh, app.RiskBand)
	ms.AssertExpectations(t)
}

func Test_submit_application_should_set_submitted_by_when_user_is_provided(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	app, _, err := newSvc(ms).SubmitApplication(validRequest(), "mihika")

	require.NoError(t, err)
	assert.Equal(t, "mihika", app.SubmittedBy)
	ms.AssertExpectations(t)
}

func Test_submit_application_should_set_loan_type_when_loan_type_is_provided(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	req := validRequest()
	req.LoanType = "home"

	app, _, err := newSvc(ms).SubmitApplication(req, "u")

	require.NoError(t, err)
	assert.Equal(t, models.LoanHome, app.LoanType)
	ms.AssertExpectations(t)
}

func Test_submit_application_should_call_save_and_update_once_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	_, _, err := newSvc(ms).SubmitApplication(validRequest(), "u")

	require.NoError(t, err)
	ms.AssertNumberOfCalls(t, "Save", 1)
	ms.AssertNumberOfCalls(t, "Update", 1)
}

func Test_submit_application_should_populate_pipeline_summary_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	_, summary, err := newSvc(ms).SubmitApplication(validRequest(), "u")

	require.NoError(t, err)
	require.NotNil(t, summary)
	assert.Greater(t, summary.CreditScore, 0.0)
	assert.GreaterOrEqual(t, summary.FraudProbability, 0.0)
	assert.LessOrEqual(t, summary.FraudProbability, 1.0)
}

func Test_submit_application_should_set_status_not_pending_when_policy_unavailable(t *testing.T) {

	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	app, _, err := newSvc(ms).SubmitApplication(validRequest(), "u")

	require.NoError(t, err)
	assert.NotEqual(t, models.StatusPending, app.Status)
}

func Test_submit_application_should_calculate_debt_to_income_in_summary_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}
	setupSubmitMocks(ms)

	req := validRequest()
	req.MonthlyEMIs = 5000
	req.AnnualIncome = 1200000

	_, summary, err := newSvc(ms).SubmitApplication(req, "u")

	require.NoError(t, err)
	assert.InDelta(t, 0.05, summary.DebtToIncome, 0.001)
}

func Test_get_application_should_return_app_when_found(t *testing.T) {
	ms := &mocks.MockStorer{}
	expected := &models.LoanApplication{ID: 1, ApplicantName: "Arjun"}
	ms.On("Get", 1).Return(expected, true)

	app, ok := newSvc(ms).GetApplication(1)

	assert.True(t, ok)
	assert.Equal(t, expected.ID, app.ID)
	ms.AssertExpectations(t)
}

func Test_get_application_should_return_false_when_not_found(t *testing.T) {
	ms := &mocks.MockStorer{}
	ms.On("Get", 999).Return(nil, false)

	_, ok := newSvc(ms).GetApplication(999)

	assert.False(t, ok)
	ms.AssertExpectations(t)
}

func Test_list_applications_should_return_all_when_no_filter(t *testing.T) {
	ms := &mocks.MockStorer{}
	apps := []*models.LoanApplication{{ID: 1}, {ID: 2}}
	ms.On("List", "").Return(apps)

	result := newSvc(ms).ListApplications("")

	assert.Len(t, result, 2)
	ms.AssertExpectations(t)
}

func Test_list_applications_should_return_filtered_when_status_filter_is_passed(t *testing.T) {
	ms := &mocks.MockStorer{}
	ms.On("List", "approved").Return([]*models.LoanApplication{{ID: 1}})

	result := newSvc(ms).ListApplications("approved")

	assert.Len(t, result, 1)
	ms.AssertCalled(t, "List", "approved")
}

func Test_list_applications_should_return_empty_slice_when_no_results(t *testing.T) {
	ms := &mocks.MockStorer{}
	ms.On("List", "rejected").Return([]*models.LoanApplication{})

	result := newSvc(ms).ListApplications("rejected")

	assert.Empty(t, result)
}

func Test_update_status_should_return_updated_app_when_id_is_valid(t *testing.T) {
	ms := &mocks.MockStorer{}
	updated := &models.LoanApplication{ID: 1, Status: models.StatusDisbursed}
	ms.On("UpdateStatus", 1, models.StatusDisbursed, "funds sent").Return(updated, true)

	app, ok := newSvc(ms).UpdateStatus(1, models.StatusDisbursed, "funds sent")

	assert.True(t, ok)
	assert.Equal(t, models.StatusDisbursed, app.Status)
	ms.AssertExpectations(t)
}

func Test_update_status_should_return_false_when_id_is_invalid(t *testing.T) {
	ms := &mocks.MockStorer{}
	ms.On("UpdateStatus", 999, mock.Anything, mock.Anything).Return(nil, false)

	_, ok := newSvc(ms).UpdateStatus(999, models.StatusApproved, "")

	assert.False(t, ok)
	ms.AssertExpectations(t)
}

func Test_stats_should_delegate_to_store_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}
	expected := map[string]any{"total_applications": 5}
	ms.On("Stats").Return(expected)

	result := newSvc(ms).Stats()

	assert.Equal(t, expected, result)
	ms.AssertExpectations(t)
}

func Test_calculate_emi_should_return_correct_values_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}

	result, err := newSvc(ms).CalculateEMI(500000, 12, 24)

	require.NoError(t, err)
	assert.InDelta(t, 23537.0, result.MonthlyEMI, 10.0)
	assert.Greater(t, result.TotalPayable, result.MonthlyEMI)
	assert.Greater(t, result.TotalInterest, 0.0)
}

func Test_calculate_emi_should_return_total_payable_equals_emi_times_months_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}

	result, err := newSvc(ms).CalculateEMI(300000, 10, 12)

	require.NoError(t, err)
	assert.InDelta(t, result.MonthlyEMI*12, result.TotalPayable, 1.0)
}

func Test_calculate_emi_should_return_positive_total_interest_when_called(t *testing.T) {
	ms := &mocks.MockStorer{}

	result, err := newSvc(ms).CalculateEMI(200000, 8, 18)

	require.NoError(t, err)
	assert.Greater(t, result.TotalInterest, 0.0)
	assert.InDelta(t, result.TotalPayable-200000, result.TotalInterest, 1.0)
}
