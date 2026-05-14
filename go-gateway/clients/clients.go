package clients

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"time"

	"loan-risk/models"
)

var httpClient = &http.Client{Timeout: 15 * time.Second}

var (
	pythonURL = getEnv("PYTHON_BASE_URL", "http://python-scorer:8000")
	javaURL   = getEnv("JAVA_BASE_URL", "http://java-engine:8081")
)

func getEnv(key, fallback string) string {
	value := os.Getenv(key)

	if value == "" {
		return fallback
	}

	return value
}

func postJSON(url string, payload any, target any) error {
	data, err := json.Marshal(payload)
	if err != nil {
		return fmt.Errorf("marshal: %w", err)
	}
	resp, err := httpClient.Post(url, "application/json", bytes.NewReader(data))
	if err != nil {
		return fmt.Errorf("POST %s: %w", url, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		body, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("%s returned %d: %s", url, resp.StatusCode, body)
	}
	return json.NewDecoder(resp.Body).Decode(target)
}

func GetCreditScore(req models.CreditScoreRequest) (*models.CreditScoreResponse, error) {
	var result models.CreditScoreResponse
	if err := postJSON(pythonURL+"/score/credit-risk", req, &result); err != nil {
		return nil, fmt.Errorf("python credit-score: %w", err)
	}
	return &result, nil
}

func CheckFraud(req models.FraudCheckRequest) (*models.FraudCheckResponse, error) {
	var result models.FraudCheckResponse
	if err := postJSON(pythonURL+"/score/fraud-check", req, &result); err != nil {
		return nil, fmt.Errorf("python fraud-check: %w", err)
	}
	return &result, nil
}

func EvaluatePolicy(req models.PolicyEvalRequest) (*models.PolicyEvalResponse, error) {
	var result models.PolicyEvalResponse
	if err := postJSON(javaURL+"/engine/evaluate", req, &result); err != nil {
		return nil, fmt.Errorf("java policy-eval: %w", err)
	}
	return &result, nil
}

func CalculateEMI(req models.EMIRequest) (*models.EMIResponse, error) {
	var result models.EMIResponse
	if err := postJSON(javaURL+"/engine/emi", req, &result); err != nil {
		return nil, fmt.Errorf("java emi-calc: %w", err)
	}
	return &result, nil
}
